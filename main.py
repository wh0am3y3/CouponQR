import os
import secrets
import qrcode
from flask import Flask, render_template_string, request, redirect, url_for, send_file
from flask_sqlalchemy import SQLAlchemy
from io import BytesIO

# App initialization
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///coupons.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Models
class Coupon(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(50), unique=True, nullable=False)
    is_used = db.Column(db.Boolean, default=False, nullable=False)

# Templates
INDEX_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Coupon Manager</title>
</head>
<body>
    <h1>Coupon Manager</h1>
    <h2>Generate New Coupon</h2>
    <form method="post" action="{{ url_for('index') }}">
        <button type="submit">Generate Coupon</button>
    </form>
    <h2>Existing Coupons</h2>
    <table border="1">
        <tr>
            <th>ID</th>
            <th>Code</th>
            <th>Used</th>
            <th>Redeem URL</th>
            <th>QR Code</th>
        </tr>
        {% for coupon in coupons %}
        <tr>
            <td>{{ coupon.id }}</td>
            <td>{{ coupon.code }}</td>
            <td>{{ 'Yes' if coupon.is_used else 'No' }}</td>
            <td><a href="{{ url_for('redeem', code=coupon.code, _external=True) }}">{{ url_for('redeem', code=coupon.code, _external=True) }}</a></td>
            <td><a href="{{ url_for('qr_code', coupon_id=coupon.id) }}">View QR</a></td>
        </tr>
        {% endfor %}
    </table>
</body>
</html>
"""

REDEEM_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Redeem Coupon</title>
</head>
<body>
    <h1>Redeem Coupon</h1>
    <p>{{ message }}</p>
    <a href="{{ url_for('index') }}">Back to Home</a>
</body>
</html>
"""

# Routes
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        new_code = secrets.token_hex(8)
        new_coupon = Coupon(code=new_code)
        db.session.add(new_coupon)
        db.session.commit()
        return redirect(url_for('index'))
    
    coupons = Coupon.query.all()
    return render_template_string(INDEX_TEMPLATE, coupons=coupons)

@app.route('/redeem')
def redeem():
    code = request.args.get('code')
    if not code:
        return render_template_string(REDEEM_TEMPLATE, message="No coupon code provided.")

    coupon = Coupon.query.filter_by(code=code).first()

    if not coupon:
        return render_template_string(REDEEM_TEMPLATE, message="Invalid coupon code.")

    if coupon.is_used:
        return render_template_string(REDEEM_TEMPLATE, message="This coupon has already been used.")

    coupon.is_used = True
    db.session.commit()
    return render_template_string(REDEEM_TEMPLATE, message="Coupon redeemed successfully!")

@app.route('/qrcode/<int:coupon_id>')
def qr_code(coupon_id):
    coupon = Coupon.query.get_or_404(coupon_id)
    redeem_url = url_for('redeem', code=coupon.code, _external=True)
    
    img_io = BytesIO()
    qr_img = qrcode.make(redeem_url)
    qr_img.save(img_io, 'PNG')
    img_io.seek(0)
    
    return send_file(img_io, mimetype='image/png')

def main():
    with app.app_context():
        db.create_all()
    # To run the app, use the command: flask run
    print("Database initialized. To run the app, execute 'flask run' in your terminal.")
    print("You may need to set the FLASK_APP environment variable: export FLASK_APP=main")


if __name__ == "__main__":
    main()