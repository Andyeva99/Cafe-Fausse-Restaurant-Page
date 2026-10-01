import os, random
from datetime import datetime, timezone
import psycopg2
from flask import Flask, jsonify, request
from flask_cors import CORS
from dotenv import load_dotenv
from email_validator import validate_email, EmailNotValidError

load_dotenv()
app=Flask(__name__); CORS(app)
DB=os.getenv('DATABASE_URL'); PORT=int(os.getenv('PORT','5000')); TABLES=30

def conn(): return psycopg2.connect(DB)
def email(v): return str(v or '').strip().lower()
def slot(v): return datetime.fromisoformat(v).replace(tzinfo=timezone.utc)

@app.get('/api/health')
def health():
 try:
  with conn() as c: c.cursor().execute('SELECT 1')
  return jsonify(status='ok')
 except Exception: return jsonify(status='error'),503

@app.get('/api/availability')
def availability():
 d=request.args.get('date'); t=request.args.get('time')
 if not d or not t: return jsonify(error='date and time are required'),400
 try: s=slot(f'{d}T{t}')
 except ValueError: return jsonify(error='Invalid date/time'),400
 with conn() as c:
  with c.cursor() as q:
   q.execute('SELECT table_number FROM reservations WHERE time_slot=%s',(s,)); used={r[0] for r in q.fetchall()}
 return jsonify(available_tables=TABLES-len(used),total_tables=TABLES,available=len(used)<TABLES)

@app.post('/api/reservations')
def reserve():
 x=request.get_json(silent=True) or {}; name=str(x.get('customerName','')).strip(); e=email(x.get('email')); phone=str(x.get('phone','')).strip() or None
 try: guests=int(x.get('guests'))
 except: guests=0
 d=str(x.get('date','')); t=str(x.get('time',''))
 if not name: return jsonify(error='Customer name is required.'),400
 if guests<1 or guests>20: return jsonify(error='Number of guests must be between 1 and 20.'),400
 if not d or not t: return jsonify(error='Please select a date and time.'),400
 try: validate_email(e,check_deliverability=False); s=slot(f'{d}T{t}')
 except (EmailNotValidError,ValueError): return jsonify(error='Please provide a valid email and date/time.'),400
 if s<=datetime.now(timezone.utc): return jsonify(error='Please choose a future reservation time.'),400
 c=conn()
 try:
  with c:
   with c.cursor() as q:
    q.execute('''INSERT INTO customers(customer_name,customer_email,phone_number) VALUES(%s,%s,%s)
      ON CONFLICT(customer_email) DO UPDATE SET customer_name=EXCLUDED.customer_name, phone_number=COALESCE(EXCLUDED.phone_number,customers.phone_number)
      RETURNING customer_id''',(name,e,phone)); cid=q.fetchone()[0]
    q.execute('SELECT table_number FROM reservations WHERE time_slot=%s FOR UPDATE',(s,)); used={r[0] for r in q.fetchall()}; free=[n for n in range(1,TABLES+1) if n not in used]
    if not free: return jsonify(error='That time slot is fully booked. Please choose another time.'),409
    table=random.choice(free)
    q.execute('INSERT INTO reservations(customer_id,time_slot,table_number,number_of_guests) VALUES(%s,%s,%s,%s) RETURNING reservation_id',(cid,s,table,guests)); rid=q.fetchone()[0]
  return jsonify(message='Reservation confirmed.',reservationId=rid,tableNumber=table),201
 except psycopg2.errors.UniqueViolation:
  c.rollback(); return jsonify(error='That table was just taken. Please try again.'),409
 finally: c.close()

@app.post('/api/newsletter')
def newsletter():
 e=email((request.get_json(silent=True) or {}).get('email'))
 try: validate_email(e,check_deliverability=False)
 except EmailNotValidError: return jsonify(error='Please enter a valid email address.'),400
 with conn() as c:
  with c.cursor() as q:
   q.execute('INSERT INTO newsletter_signups(email) VALUES(%s) ON CONFLICT(email) DO NOTHING',(e,))
   q.execute('UPDATE customers SET newsletter_signup=TRUE WHERE customer_email=%s',(e,))
 return jsonify(message="You're on the list. Welcome to Café Fausse."),201

if __name__=='__main__': app.run(host='0.0.0.0',port=PORT,debug=True)
