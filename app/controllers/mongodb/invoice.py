from flask import Blueprint, request, jsonify, current_app
import requests
import json
from bson import ObjectId
import os
from datetime import datetime, timedelta
import pytz
from app.celery_app import celery
from app.middleware import role_required

invoice_controller = Blueprint("invoice_controller", __name__)

# Configuration
XENDIT_API_KEY = os.getenv('XENDIT_API_KEY')
WA_URI = os.getenv('WA_TEST')
WA_TOKEN = os.getenv('WA_TOKEN')


@invoice_controller.route("/create_invoice", methods=["POST"])
def create_invoice():
    try:
        db = current_app.config['db']
        collection = db.invoice
        order_data = request.json

        # Validate order data
        if not order_data.get('reservationCode') or not order_data.get('reservation'):
            return jsonify({"errorMessage": "Missing required reservation data"}), 400

        # Extract data
        reservationCode = order_data.get('reservationCode', '')
        reservation = order_data.get('reservation', {})
        reservationId = reservation.get('reservationId', '')
        branchCode = reservation.get('branchCode', '')
        branch = reservation.get('branchName', '')
        totalAmount = reservation.get('totalAmount', 0)
        customer = reservation.get('customer', {})
        name = customer.get('name', '')
        phone = customer.get('phone', '')
        email = customer.get('email', '')
        formatted_amount = f"{totalAmount:,.0f}"

        # Xendit API Payload
        url = "https://api.xendit.co/v2/invoices"
        payload = {
            "external_id": f"order-{order_data.get('order_id')}",
            "amount": totalAmount,
            "description": branch,
            "payer_email": email,
            "should_send_email": True,
            "invoice_duration": 900
        }
        headers = {
            "Authorization": f"Basic {XENDIT_API_KEY}",
            "Content-Type": "application/json"
        }

        # Send request to Xendit
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        response_data = response.json()

        if response.status_code == 200 and "id" in response_data:
            invoice_id = response_data["id"]
            invoice_url = response_data["invoice_url"]
            external_id = response_data["external_id"]
            expiry_date_utc = response_data["expiry_date"]

            # Convert expiry_date to WIB
            utc_zone = pytz.utc
            jakarta_zone = pytz.timezone('Asia/Jakarta')
            expiry_date_utc_parsed = datetime.strptime(expiry_date_utc, '%Y-%m-%dT%H:%M:%S.%fZ')
            expiry_date_utc_parsed = expiry_date_utc_parsed.replace(tzinfo=utc_zone)
            expiry_date_wib = expiry_date_utc_parsed.astimezone(jakarta_zone)
            expiry_time_formatted = expiry_date_wib.strftime("%H:%M")

            # Schedule reminders and expiration tasks
            reminder_time = expiry_date_wib - timedelta(minutes=5)
            send_whatsapp_reminder.apply_async(
                args=[phone, name, branch, reservationCode, expiry_date_wib, formatted_amount],
                eta=reminder_time
            )
            expire_invoice.apply_async(
                args=[invoice_id, reservationId],
                eta=expiry_date_wib
            )

            # Save invoice data to MongoDB
            invoice_data = {
                "invoice_id": invoice_id,
                "branchCode": branchCode,
                "reservationCode": reservationCode,
                "reservation": reservation,
                "expiry_date": expiry_date_utc,
                "invoice_url": invoice_url,
                "external_id": external_id,
                "status": "Menunggu Pembayaran",
                "createdAt": datetime.utcnow(),
            }
            collection.insert_one(invoice_data)

            # Send WhatsApp message for payment
            send_payment_whatsapp.apply_async(
                args=[phone, name, branch, reservationCode, expiry_time_formatted, formatted_amount, invoice_id]
            )

            return jsonify({
                "invoice_id": invoice_id,
                "invoice_url": invoice_url,
                "message": "Invoice created successfully and WhatsApp will be sent"
            }), 200
        else:
            return jsonify({"message": "Failed to create invoice", "error": response_data}), response.status_code

    except requests.exceptions.RequestException as req_err:
        print(f"Request error: {req_err}")
        return jsonify({"errorMessage": f"Request error: {req_err}"}), 500
    except Exception as e:
        print(f"Error in create_invoice: {e}")
        return jsonify({"errorMessage": f"Error in create_invoice: {e}"}), 500


@celery.task
def send_payment_whatsapp(phone, name, branch, reservationCode, expiry_time_formatted, formatted_amount, invoice_id):
    try:
        whatsapp_url = WA_URI
        whatsapp_headers = {
            "Authorization": f"Bearer {WA_TOKEN}",
            "Content-Type": "application/json"
        }
        whatsapp_payload = {
            "messaging_product": "whatsapp",
            "to": phone,
            "type": "template",
            "template": {
                "name": "invoice_template",
                "language": {"code": "en"},
                "components": [
                    {
                        "type": "body",
                        "parameters": [
                            {"type": "text", "text": name},
                            {"type": "text", "text": branch},
                            {"type": "text", "text": reservationCode},
                            {"type": "text", "text": expiry_time_formatted},
                            {"type": "text", "text": formatted_amount}
                        ]
                    },
                    {
                        "type": "button",
                        "sub_type": "url",
                        "index": 0,
                        "parameters": [{"type": "text", "text": invoice_id}]
                    }
                ]
            }
        }
        response = requests.post(whatsapp_url, headers=whatsapp_headers, data=json.dumps(whatsapp_payload), timeout=10)
        if response.status_code == 200:
            print("WhatsApp message for payment sent successfully")
        else:
            print("Failed to send WhatsApp for payment:", response.json())
    except Exception as e:
        print(f"Error in send_payment_whatsapp: {e}")


@celery.task
def expire_invoice(invoice_id, reservationId):
    try:
        app = celery.app  # Ambil aplikasi Flask
        if app is None:
            print("Flask app is not attached to Celery!")
            return
        with app.app_context():  # Gunakan Application Context Flask
            db = app.config['db']
            collection_invoice = db.invoice
            collection_reservation = db.reservation

            # Update status invoice dan reservasi
            collection_invoice.update_one(
                {"invoice_id": invoice_id, "status": "Menunggu Pembayaran"},
                {"$set": {"status": "Expired"}}
            )
            collection_reservation.update_one(
                {"_id": ObjectId(reservationId), "status": "PENDING"},
                {"$set": {"status": "EXPIRED"}}
            )
            print(f"Invoice {invoice_id} and Reservation {reservationId} marked as EXPIRED")
    except Exception as e:
        print(f"Error in expire_invoice: {e}")

@celery.task
def send_whatsapp_reminder(phone, name, branch, reservationCode, expiry_date_wib, formatted_amount):
    try:
        app = celery.app  # Ambil aplikasi Flask yang sudah ditambahkan ke Celery
        with app.app_context():  # Bungkus dalam Application Context
            db = app.config['db']
            collection_invoice = db.invoice

            # Cek status pembayaran
            invoice = collection_invoice.find_one({"reservationCode": reservationCode})
            if invoice and invoice.get("status") == "Lunas":
                print(f"Reminder tidak dikirim karena pembayaran untuk {reservationCode} sudah lunas.")
                return

            # Kirim WhatsApp
            whatsapp_url = WA_URI
            whatsapp_headers = {
                "Authorization": f"Bearer {WA_TOKEN}",
                "Content-Type": "application/json"
            }
            whatsapp_payload = {
                "messaging_product": "whatsapp",
                "to": phone,
                "type": "template",
                "template": {
                    "name": "reminder_payment",
                    "language": {"code": "en"},
                    "components": [
                        {"type": "body", "parameters": [
                            {"type": "text", "text": name},
                            {"type": "text", "text": branch},
                            {"type": "text", "text": expiry_date_wib.strftime("%H:%M")},
                            {"type": "text", "text": formatted_amount},
                            {"type": "text", "text": reservationCode}
                        ]}
                    ]
                }
            }
            response = requests.post(whatsapp_url, headers=whatsapp_headers, data=json.dumps(whatsapp_payload))
            if response.status_code == 200:
                print("Reminder WhatsApp message sent successfully")
            else:
                print("Failed to send WhatsApp reminder:", response.json())
    except Exception as e:
        print(f"Error in send_whatsapp_reminder: {e}")

@invoice_controller.route("/xendit_webhook", methods=["POST"])
def xendit_webhook():
    try:
        db = current_app.config['db']
        collection_invoice = db.invoice
        collection_reservation = db.reservation
        counters_collection = db.counters

        data = request.json

        # Extract Xendit data
        invoice_id = data.get("id")
        status = data.get("status")
        reservation_id = data.get("external_id").split("-")[-1]
        paid_at = data.get("paid_at")
        updated_at = data.get("updated")
        payment_method = data.get("payment_method")
        payment_channel = data.get("payment_channel")
        payment_destination = data.get("payment_destination")
        paid_amount = data.get("paid_amount")
        currency = data.get("currency")
        bank_code = data.get("bank_code")
        merchant_name = data.get("merchant_name")

        # Generate receipt link
        receipt = f"https://kc4908tb-5173.asse.devtunnels.ms/invoice/{reservation_id}"

        # Update invoice data
        invoice_data = {
            "status": "Lunas" if status == "PAID" else status,
            "paid_at": paid_at,
            "updated_at": updated_at,
            "payment_method": payment_method,
            "payment_channel": payment_channel,
            "payment_destination": payment_destination,
            "paid_amount": paid_amount,
            "currency": currency,
            "bank_code": bank_code,
            "merchant_name": merchant_name,
            "refund_status": "Not Requested"  # Default value
        }

        result = collection_invoice.update_one(
            {"invoice_id": invoice_id},
            {"$set": invoice_data}
        )

        if result.modified_count > 0:
            reservation_object_id = ObjectId(reservation_id)

            # Update reservation status to PAID
            update_reservation_data = {
                "status": "PAID",
                "arrivalStatus": "Pending Confirmation"
            }

            # Generate tableName if status changes to PAID
            reservation = collection_reservation.find_one({"_id": reservation_object_id})
            if status == "PAID" and reservation:
                branchCode = reservation.get("branchCode")
                reservation_date = reservation.get("date")

                if branchCode and reservation_date:
                    table_name = generate_table_name(branchCode, reservation_date, counters_collection)
                    update_reservation_data["tableName"] = table_name

            collection_reservation.update_one(
                {"_id": reservation_object_id},
                {"$set": update_reservation_data}
            )

            # Fetch customer data for WhatsApp message
            branch = reservation.get("branchName", "")
            reservationCode = reservation.get("reservationCode", "")
            date = reservation.get("date", "")
            time = reservation.get("time", "")
            guest = reservation.get("guest", "")
            customer = reservation.get("customer", {})
            phone = customer.get("phone", "")
            name = customer.get("name", "")

            # Format date
            def format_date(date_str):
                date_obj = datetime.strptime(date_str, "%Y-%m-%d")
                return date_obj.strftime("%-d %B %Y")

            formatted_date = format_date(date)

            # Send payment confirmation WhatsApp via Celery
            send_payment_confirmation_whatsapp.apply_async(
                args=[
                    phone, name, branch, reservationCode, formatted_date, time, guest, receipt
                ]
            )

            print(f"Invoice {invoice_id} and Reservation {reservation_id} updated successfully.")
        else:
            print(f"Invoice {invoice_id} update failed or no changes made.")

        return jsonify({"message": "Webhook received"}), 200
    except Exception as e:
        print(f"Error in xendit_webhook: {e}")
        return jsonify({"errorMessage": f"Error in xendit_webhook: {e}"}), 500


@celery.task
def send_payment_confirmation_whatsapp(phone, name, branch, reservationCode, formatted_date, time, guest, receipt):
    try:
        whatsapp_url = WA_URI
        whatsapp_headers = {
            "Authorization": f"Bearer {WA_TOKEN}",
            "Content-Type": "application/json"
        }
        whatsapp_payload = {
            "messaging_product": "whatsapp",
            "to": phone,
            "type": "template",
            "template": {
                "name": "payment_confirmation",
                "language": {"code": "en"},
                "components": [
                    {
                        "type": "body",
                        "parameters": [
                            {"type": "text", "text": name},
                            {"type": "text", "text": formatted_date},
                            {"type": "text", "text": time},
                            {"type": "text", "text": guest},
                            {"type": "text", "text": branch},
                            {"type": "text", "text": reservationCode},
                            {"type": "text", "text": receipt},
                        ]
                    }
                ]
            }
        }

        response = requests.post(whatsapp_url, headers=whatsapp_headers, data=json.dumps(whatsapp_payload), timeout=10)
        if response.status_code == 200:
            print("Payment confirmation WhatsApp message sent successfully.")
        else:
            print("Failed to send payment confirmation WhatsApp message:", response.json())
    except Exception as e:
        print(f"Error in send_payment_confirmation_whatsapp: {e}")

def generate_table_name(branchCode, date, counters_collection):
    # Format tanggal agar sesuai
    formatted_date = datetime.strptime(date, "%Y-%m-%d").strftime("%Y-%m-%d")
    
    # Gabungkan branchCode dan date sebagai unique key
    counter_key = f"{branchCode}_{formatted_date}"

    # Cari counter atau inisialisasi dengan 800
    counter = counters_collection.find_one({"_id": counter_key})
    if not counter:
        counters_collection.insert_one({"_id": counter_key, "value": 800})
        return 800

    # Jika counter sudah ada, tambahkan 1
    new_value = counters_collection.find_one_and_update(
        {"_id": counter_key},
        {"$inc": {"value": 1}},
        return_document=True
    )["value"]

    # Reset kembali ke 800 jika sudah melebihi 1100
    if new_value > 1100:
        counters_collection.update_one({"_id": counter_key}, {"$set": {"value": 800}})
        return 800
    return new_value

def send_email_smtp(to_email, subject, body):
    try:
        message = MIMEMultipart()
        message["From"] = EMAIL_ADDRESS
        message["To"] = to_email
        message["Subject"] = subject
        message.attach(MIMEText(body, "plain"))

        # Kirim email menggunakan SMTP
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            server.sendmail(EMAIL_ADDRESS, to_email, message.as_string())
        
        print(f"Email sent to {to_email} successfully.")
    except Exception as e:
        print(f"Failed to send email to {to_email}: {e}")
        
        
@invoice_controller.route("/invoice/<string:branchCode>", methods=["GET"])
@role_required(["IT", "Business Development", "Manager Accounting", "Assistant Manager Accounting", "Head Accounting", "Accounting"])
def get_invoice_by_branchCode(branchCode):
    try:
        db = current_app.config['db']
        collection = db.invoice

        invoices = collection.find({"branchCode": branchCode})

        invoice_list = []
        for invoice in invoices:
            invoice_list.append({
                "invoiceId": str(invoice["_id"]),
                "branchCode": invoice["branchCode"],
                "reservationCode": invoice.get("reservationCode", ""),
                "expiry_date": invoice.get("expiry_date"),
                "invoice_url": invoice.get("invoice_url"),
                "external_id": invoice.get("external_id"),
                "status": invoice.get("status"),
                "refund_status": invoice.get("refund_status"),
                "paid_amount": invoice.get("paid_amount", 0),
                "mdr": invoice.get("mdr", 0),
                "currency": invoice.get("currency"),
                "paid_at": invoice.get("paid_at"),
                "merchant_name": invoice.get("merchant_name"),
                "bank_code": invoice.get("bank_code"),
                "payment_channel": invoice.get("payment_channel"),
                "payment_destination": invoice.get("payment_destination"),
                "payment_method": invoice.get("payment_method"),
                "created_at" : invoice.get("createdAt"),
                "updated_at" : invoice.get("updated_at"),
            })

        if invoice_list:
            return jsonify({
                "message": "Success get invoices",
                "data": invoice_list
            }), 200
        else:
            return jsonify({"message": "No invoices found for this branch"}), 404

    except Exception as e:
        print(e)
        return jsonify({"errorMessage": str(e)}), 500
    
@invoice_controller.route("/invoices/<external_id>", methods=["PATCH"])
@role_required(["IT", "Business Development", "Manager Accounting", "Assistant Manager Accounting", "Head Accounting", "Accounting"])
def update_invoice_refund_status(external_id):
    db = current_app.config['db']
    collection_invoice = db.invoice

    data = request.json
    refund_status = data.get("refund_status")

    if not refund_status:
        return jsonify({"message": "Refund status is required"}), 400

    # Update berdasarkan external_id, bukan invoice_id
    result = collection_invoice.update_one(
        {"external_id": external_id},
        {"$set": {"refund_status": refund_status}}
    )

    if result.modified_count > 0:
        return jsonify({"message": "Refund status updated successfully"}), 200
    else:
        return jsonify({"message": "No changes made or invoice not found"}), 404