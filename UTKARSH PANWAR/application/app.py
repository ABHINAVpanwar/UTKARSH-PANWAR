from flask import Flask, request, jsonify, session, redirect, url_for, render_template
from functools import wraps
from pymongo import MongoClient
from bson import ObjectId, errors as bson_errors
from datetime import datetime, timezone, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import bleach, atexit, os, logging

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'utk-dev-secret-change-in-prod')

# ── SECURE SESSION CONFIG ─────────────────────────────────────────────────────
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax',
    SESSION_COOKIE_SECURE=os.environ.get('FLASK_ENV') == 'production',
    PERMANENT_SESSION_LIFETIME=timedelta(hours=2),
)

# ── LOGGING ───────────────────────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ── RATE LIMITER ──────────────────────────────────────────────────────────────
limiter = Limiter(key_func=get_remote_address, app=app, default_limits=[])

# ── SECURITY HEADERS ──────────────────────────────────────────────────────────
@app.after_request
def set_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    response.headers['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'
    response.headers['Content-Security-Policy'] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' https://cdnjs.cloudflare.com https://fonts.googleapis.com; "
        "style-src 'self' 'unsafe-inline' https://cdnjs.cloudflare.com https://fonts.googleapis.com https://fonts.gstatic.com; "
        "font-src 'self' https://cdnjs.cloudflare.com https://fonts.gstatic.com; "
        "img-src 'self' data: https:; "
        "frame-src https://player.vimeo.com https://www.youtube.com https://www.youtube-nocookie.com "
                   "https://youtube.com https://www.facebook.com; "
        "media-src 'self'; "
        "connect-src 'self' https://player.vimeo.com https://f.vimeocdn.com https://fresnel.vimeocdn.com https://api.open-meteo.com;"
    )
    return response

# ── AUTH ──────────────────────────────────────────────────────────────────────
ADMIN_USERNAME      = os.environ.get('ADMIN_USERNAME', 'utkarsh')
ADMIN_PASSWORD_HASH = generate_password_hash(
    os.environ.get('ADMIN_PASSWORD', 'utk@1234')
)

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('logged_in'):
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

def safe_object_id(oid):
    """Return ObjectId or None if invalid — prevents 500 crashes."""
    try:
        return ObjectId(oid)
    except (bson_errors.InvalidId, TypeError):
        return None

def sanitize(text, max_len=2000):
    """Strip all HTML tags and limit length."""
    return bleach.clean(str(text), tags=[], strip=True)[:max_len]

# ── MONGODB ───────────────────────────────────────────────────────────────────
MONGO_URI    = os.environ.get(
    'MONGO_URI',
    'mongodb+srv://utkarsh:utk1234@cluster0.koygnga.mongodb.net/?appName=Cluster0'
)
MONGO_DB_NAME = os.environ.get('MONGO_DB_NAME', 'utk_portfolio')
WEB3FORMS_KEY = os.environ.get('WEB3FORMS_KEY', '4d6d075d-2a50-465e-acb1-6e59d6039eb6')

try:
    mongo_client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    mongo_client.admin.command('ping')
    db           = mongo_client[MONGO_DB_NAME]
    about_col    = db['about']
    credits_col  = db['credits']
    work_col     = db['work']
    messages_col = db['messages']
    visits_col   = db['visits']
    skills_col   = db['skills']
    awards_col   = db['awards']
    blogs_col    = db['blogs']
    timeline_col = db['timeline']
    companies_col = db['companies']
    ratings_col  = db['ratings']
    stills_col   = db['stills']
    logger.info("✅ MongoDB connected successfully!")
except Exception as e:
    logger.error(f"❌ MongoDB connection failed: {e}")
    db = about_col = credits_col = work_col = messages_col = visits_col = skills_col = awards_col = blogs_col = timeline_col = companies_col = ratings_col = stills_col = None

atexit.register(lambda: mongo_client.close() if mongo_client is not None else None)

@app.route('/api/config')
def get_config():
    return jsonify({'web3forms_key': WEB3FORMS_KEY})

# ── SEED DEFAULT DATA ─────────────────────────────────────────────────────────
def seed():
    if about_col is None:
        logger.warning("Skipping seed - MongoDB not connected")
        return

    if not about_col.find_one({'_id': 'about'}):
        about_col.insert_one({
            '_id': 'about',
            'role': 'FX TD · DNEG',
            'hero_tag': 'FX TD @ DNEG',
            'hero_desc': 'Versatile Visual Effects Artist — transforming imagination into cinematic reality through Houdini, Nuke & beyond.',
            'exp_hours': 10000,
            'email': 'utkarshpanwar01@gmail.com',
            'phone': '+91 8810669600',
            'showreel': 'https://player.vimeo.com/video/836954122?h=351a362af3&autoplay=1&title=0&byline=0&portrait=0',
            'social_links': {
                'linkedin': 'https://www.linkedin.com/in/utkarsh-panwar/',
                'vimeo': 'https://vimeo.com/user146712461',
                'resume': '',
                'artstation': 'https://www.artstation.com/utkarshpanwar11',
                'instagram': 'https://www.instagram.com/utkarshpanwar11/',
            },
            'cards': [
                {'icon': 'fa-regular fa-user', 'title': 'WHO AM I', 'text': 'VFX artist with 3+ years of studio experience, currently an FX TD at DNEG bringing imagination to life through cutting-edge visual effects.'},
                {'icon': 'fa-solid fa-tv', 'title': 'WHAT I DO', 'text': 'FX and Compositing — creating realistic simulations in Houdini and integrating them seamlessly in Nuke for cinematic storytelling.'},
                {'icon': 'fa-solid fa-gears', 'title': 'MY TOOLS', 'text': 'Houdini · Nuke · Maya · 3ds Max — combining technical precision with creative artistry to craft high-quality visual effects.'},
                {'icon': 'fa-solid fa-location-dot', 'title': 'WHERE', 'text': 'Originally from Delhi, currently contributing to world-class VFX productions at DNEG.'},
            ]
        })
        logger.info("Seeded About data")

seed()

# ── ONE-TIME MIGRATIONS ───────────────────────────────────────────────────────
def migrate():
    if credits_col is None:
        return
    doc = credits_col.find_one({'category': 'Other Projects'})
    if doc and not any(v.get('caption') == 'Retro Shoes' for v in doc.get('videos', [])):
        credits_col.update_one(
            {'category': 'Other Projects'},
            {'$push': {'videos': {'embed': 'https://www.facebook.com/plugins/video.php?height=314&href=https%3A%2F%2Fwww.facebook.com%2FDelhiCgAnimationAwards%2Fvideos%2F3412812522314542%2F&show_text=false&width=560&t=0', 'caption': 'Retro Shoes'}}}
        )

migrate()

# ── VISITOR LOGGING ───────────────────────────────────────────────────────────
SKIP_PATHS = {'/static', '/api', '/favicon'}
SKIP_UA    = {'Mozilla/5.0+(compatible; UptimeRobot/2.0; http://www.uptimerobot.com/)'}
BOT_FILTER = {'ua': {'$nin': list(SKIP_UA)}}

@app.before_request
def log_visit():
    if visits_col is None:
        return
    path = request.path
    if any(path.startswith(p) for p in SKIP_PATHS):
        return
    if request.headers.get('User-Agent', '') in SKIP_UA:
        return
    visitor_name = sanitize(request.cookies.get('utk_vname') or '', max_len=80)
    referrer     = sanitize(request.headers.get('Referer') or '', max_len=300)
    visits_col.insert_one({
        'ip':       request.headers.get('X-Forwarded-For', request.remote_addr).split(',')[0].strip()[:45],
        'name':     visitor_name or None,
        'path':     path[:200],
        'referrer': referrer or None,
        'ua':       request.headers.get('User-Agent', '')[:200],
        'ts':       datetime.now(timezone.utc),
    })

@app.route('/api/admin/visits')
@login_required
def get_visits():
    if visits_col is None:
        return jsonify([]), 500
    page     = max(1, int(request.args.get('page', 1)))
    per_page = 50
    total    = visits_col.count_documents(BOT_FILTER)
    docs     = list(visits_col.find(BOT_FILTER).sort('ts', -1).skip((page - 1) * per_page).limit(per_page))
    for d in docs:
        d['_id'] = str(d['_id'])
        d['ts']  = d['ts'].strftime('%Y-%m-%dT%H:%M:%SZ') if d.get('ts') else ''
    return jsonify({'visits': docs, 'total': total, 'page': page, 'pages': -(-total // per_page)})

@app.route('/api/admin/visits/stats')
@login_required
def visit_stats():
    if visits_col is None:
        return jsonify({}), 500
    total      = visits_col.count_documents(BOT_FILTER)
    today      = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0, tzinfo=timezone.utc)
    today_count = visits_col.count_documents({**BOT_FILTER, 'ts': {'$gte': today}})
    week_count  = visits_col.count_documents({**BOT_FILTER, 'ts': {'$gte': today - timedelta(days=7)}})
    top_pages   = list(visits_col.aggregate([
        {'$match': BOT_FILTER},
        {'$group': {'_id': '$path', 'count': {'$sum': 1}}},
        {'$sort': {'count': -1}}, {'$limit': 5}
    ]))
    unique_ips  = len(visits_col.distinct('ip', BOT_FILTER))
    return jsonify({'total': total, 'today': today_count, 'week': week_count,
                    'unique_ips': unique_ips, 'top_pages': top_pages})

@app.route('/api/admin/visits', methods=['DELETE'])
@login_required
def clear_visits():
    if visits_col is None:
        return jsonify({}), 500
    visits_col.delete_many({})
    return jsonify({'status': 'cleared'})

# ── RATINGS API ─────────────────────────────────────────────────────────────
@app.route('/api/ratings', methods=['GET'])
def get_ratings():
    """Get average rating and total count"""
    if ratings_col is None:
        return jsonify({'average': 0, 'total': 0}), 500
    
    # Get all ratings
    all_ratings = list(ratings_col.find({}, {'value': 1}))
    total = len(all_ratings)
    
    if total == 0:
        return jsonify({'average': 0, 'total': 0, 'stars': [0,0,0,0,0]})
    
    # Calculate average
    avg = sum(r['value'] for r in all_ratings) / total
    
    # Calculate distribution (how many of each star)
    distribution = [0, 0, 0, 0, 0]
    for r in all_ratings:
        if 1 <= r['value'] <= 5:
            distribution[r['value'] - 1] += 1
    
    return jsonify({
        'average': round(avg, 1),
        'total': total,
        'distribution': distribution
    })

@app.route('/api/ratings', methods=['POST'])
@limiter.limit('3 per hour')  # Prevent spam
def submit_rating():
    """Submit a new rating"""
    if ratings_col is None:
        return jsonify({'error': 'DB unavailable'}), 500
    
    data = request.json or {}
    rating = data.get('rating')
    name = sanitize(data.get('name', 'Anonymous'), max_len=100)
    comment = sanitize(data.get('comment', ''), max_len=500)
    
    # Validate rating
    if not rating or not isinstance(rating, (int, float)):
        return jsonify({'error': 'Valid rating (1-5) required'}), 400
    
    rating = int(rating)
    if rating < 1 or rating > 5:
        return jsonify({'error': 'Rating must be between 1 and 5'}), 400
    
    # Get IP for duplicate prevention (optional)
    ip = request.headers.get('X-Forwarded-For', request.remote_addr).split(',')[0].strip()
    
    # Check if this IP already rated in last 24 hours (optional anti-spam)
    last_day = datetime.now(timezone.utc) - timedelta(hours=24)
    recent = ratings_col.count_documents({
        'ip': ip,
        'created_at': {'$gte': last_day}
    })
    
    if recent >= 2:  # Max 2 ratings per IP per day
        return jsonify({'error': 'You have reached the rating limit for today'}), 429
    
    # Save rating
    result = ratings_col.insert_one({
        'value': rating,
        'name': name,
        'comment': comment,
        'ip': ip,
        'created_at': datetime.now(timezone.utc)
    })
    
    # Get updated stats
    all_ratings = list(ratings_col.find({}, {'value': 1}))
    total = len(all_ratings)
    avg = sum(r['value'] for r in all_ratings) / total if total > 0 else 0
    
    return jsonify({
        'status': 'submitted',
        'average': round(avg, 1),
        'total': total,
        'rating_id': str(result.inserted_id)
    })

@app.route('/api/admin/ratings')
@login_required
def get_all_ratings():
    """Admin endpoint to view all ratings"""
    if ratings_col is None:
        return jsonify([]), 500
    
    ratings = list(ratings_col.find({}).sort('created_at', -1))
    for r in ratings:
        r['_id'] = str(r['_id'])
        r['created_at'] = r['created_at'].strftime('%Y-%m-%d %H:%M:%S') if r.get('created_at') else ''
        r.pop('ip', None)  # Hide IP from admin view for privacy
    
    return jsonify(ratings)

@app.route('/api/admin/ratings/<rating_id>', methods=['DELETE'])
@login_required
def delete_rating(rating_id):
    """Admin endpoint to delete a rating"""
    if ratings_col is None:
        return jsonify({'error': 'DB unavailable'}), 500
    
    oid = safe_object_id(rating_id)
    if not oid:
        return jsonify({'error': 'Invalid id'}), 400
    
    ratings_col.delete_one({'_id': oid})
    return jsonify({'status': 'deleted'})

# ── VISITOR IDENTIFY (patch current visit with name on first save) ────────────
@app.route('/api/visitor/identify', methods=['POST'])
def visitor_identify():
    if visits_col is None:
        return jsonify({}), 500
    data     = request.json or {}
    name     = sanitize(data.get('name') or '', max_len=80)
    referrer = sanitize(data.get('referrer') or '', max_len=300)
    if not name:
        return jsonify({'error': 'name required'}), 400
    ip = request.headers.get('X-Forwarded-For', request.remote_addr).split(',')[0].strip()[:45]
    update_fields = {'name': name}
    if referrer:
        update_fields['referrer'] = referrer
    visits_col.find_one_and_update(
        {'ip': ip, 'name': None},
        {'$set': update_fields},
        sort=[('ts', -1)]
    )
    # Also set cookie in response so server has it immediately on next load
    resp = jsonify({'status': 'ok'})
    resp.set_cookie('utk_vname', name, max_age=60*60*24*365, samesite='Lax', httponly=False)
    return resp

# ── MAIN SITE ─────────────────────────────────────────────────────────────────
@app.route('/')
def index():
    about   = (about_col.find_one({'_id': 'about'}, {'_id': 0}) or {}) if about_col is not None else {}
    credits = list(credits_col.find({}, {'_id': 0}).sort('order', 1)) if credits_col is not None else []
    work    = list(work_col.find({}, {'_id': 0}).sort('order', 1)) if work_col is not None else []
    companies = list(companies_col.find({}, {'_id': 0}).sort('order', 1)) if companies_col is not None else []
    ratings_stats = {'average': 0, 'total': 0}
    if ratings_col is not None:
        all_ratings = list(ratings_col.find({}, {'value': 1}))
        total = len(all_ratings)
        if total > 0:
            avg = sum(r['value'] for r in all_ratings) / total
            ratings_stats = {'average': round(avg, 1), 'total': total}

    return render_template('index.html', about=about, credits=credits, work=work, companies=companies, ratings=ratings_stats)

@app.route('/api/work/<work_id>/view', methods=['POST'])
def track_view(work_id):
    if work_col is None:
        return jsonify({}), 500
    oid = safe_object_id(work_id)
    if not oid:
        return jsonify({'error': 'Invalid id'}), 400
    work_col.update_one({'_id': oid}, {'$inc': {'views': 1}})
    return jsonify({'status': 'ok'})

# ── AUTH ROUTES ───────────────────────────────────────────────────────────────
@app.route('/login', methods=['GET', 'POST'])
@limiter.limit('10 per minute')
def login():
    error = None
    if request.method == 'POST':
        u = request.form.get('username', '').strip()
        p = request.form.get('password', '')
        if u == ADMIN_USERNAME and check_password_hash(ADMIN_PASSWORD_HASH, p):
            session.permanent = True
            session['logged_in'] = True
            return redirect(url_for('admin'))
        error = 'Invalid credentials'
    return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/admin')
@login_required
def admin():
    return render_template('admin.html')

# ── ADMIN API — ABOUT ─────────────────────────────────────────────────────────
@app.route('/api/admin/about', methods=['POST'])
@login_required
def update_about():
    if about_col is None:
        return jsonify({'error': 'DB unavailable'}), 500
    data    = request.json or {}
    allowed = {'role', 'hero_tag', 'hero_desc', 'exp_hours', 'cards', 'profile_url', 'location', 'social_links', 'email', 'phone', 'showreel'}
    update  = {k: v for k, v in data.items() if k in allowed}
    if not update:
        return jsonify({'error': 'Nothing to update'}), 400
    about_col.update_one({'_id': 'about'}, {'$set': update}, upsert=True)
    return jsonify({'status': 'updated'})

# ── ADMIN API — CREDITS ───────────────────────────────────────────────────────
@app.route('/api/admin/credits', methods=['POST'])
@login_required
def add_credit_category():
    if credits_col is None:
        return jsonify({'error': 'DB unavailable'}), 500
    data     = request.json or {}
    category = sanitize(data.get('category') or '', max_len=100)
    if not category:
        return jsonify({'error': 'category name required'}), 400
    top   = credits_col.find_one(sort=[('order', -1)])
    order = (top['order'] + 1) if top else 0
    result = credits_col.insert_one({'category': category, 'order': order, 'videos': []})
    return jsonify({'status': 'created', '_id': str(result.inserted_id)})

@app.route('/api/admin/credits/<cat_id>', methods=['PUT'])
@login_required
def update_credit_category(cat_id):
    if credits_col is None:
        return jsonify({'error': 'DB unavailable'}), 500
    oid = safe_object_id(cat_id)
    if not oid:
        return jsonify({'error': 'Invalid id'}), 400
    category = sanitize((request.json or {}).get('category', ''), max_len=100)
    if not category:
        return jsonify({'error': 'category name required'}), 400
    credits_col.update_one({'_id': oid}, {'$set': {'category': category}})
    return jsonify({'status': 'updated'})

@app.route('/api/admin/credits/<cat_id>', methods=['DELETE'])
@login_required
def delete_credit_category(cat_id):
    if credits_col is None:
        return jsonify({'error': 'DB unavailable'}), 500
    oid = safe_object_id(cat_id)
    if not oid:
        return jsonify({'error': 'Invalid id'}), 400
    credits_col.delete_one({'_id': oid})
    return jsonify({'status': 'deleted'})

@app.route('/api/admin/credits/<cat_id>/videos', methods=['POST'])
@login_required
def add_credit_video(cat_id):
    if credits_col is None:
        return jsonify({'error': 'DB unavailable'}), 500
    oid = safe_object_id(cat_id)
    if not oid:
        return jsonify({'error': 'Invalid id'}), 400
    data    = request.json or {}
    embed   = (data.get('embed') or '').strip()[:500]
    caption = sanitize(data.get('caption') or '', max_len=200)
    if not embed or not caption:
        return jsonify({'error': 'embed and caption required'}), 400
    credits_col.update_one({'_id': oid}, {'$push': {'videos': {'embed': embed, 'caption': caption}}})
    return jsonify({'status': 'added'})

@app.route('/api/admin/credits/<cat_id>/videos/<int:idx>', methods=['DELETE'])
@login_required
def delete_credit_video(cat_id, idx):
    if credits_col is None:
        return jsonify({'error': 'DB unavailable'}), 500
    oid = safe_object_id(cat_id)
    if not oid:
        return jsonify({'error': 'Invalid id'}), 400
    doc = credits_col.find_one({'_id': oid})
    if not doc:
        return jsonify({'error': 'Category not found'}), 404
    videos = doc.get('videos', [])
    if idx < 0 or idx >= len(videos):
        return jsonify({'error': 'Invalid index'}), 400
    videos.pop(idx)
    credits_col.update_one({'_id': oid}, {'$set': {'videos': videos}})
    return jsonify({'status': 'deleted'})

# ── ADMIN API — WORK (reorder MUST be before <work_id>) ──────────────────────
@app.route('/api/admin/work/reorder', methods=['POST'])
@login_required
def reorder_work():
    if work_col is None:
        return jsonify({'error': 'DB unavailable'}), 500
    order = (request.json or {}).get('order', [])
    for item in order:
        oid = safe_object_id(item.get('id'))
        if oid:
            work_col.update_one({'_id': oid}, {'$set': {'order': item['order'], 'num': str(item['order'] + 1).zfill(2)}})
    return jsonify({'status': 'reordered'})

@app.route('/api/admin/work', methods=['POST'])
@login_required
def add_work():
    if work_col is None:
        return jsonify({'error': 'DB unavailable'}), 500
    data = request.json or {}
    if not all(data.get(f) for f in ('title', 'vimeo', 'thumb', 'desc')):
        return jsonify({'error': 'title, vimeo, thumb, desc are required'}), 400
    top   = work_col.find_one(sort=[('order', -1)])
    order = (top['order'] + 1) if top else 0
    work_col.insert_one({
        'order': order,
        'num':   str(order + 1).zfill(2),
        'vimeo': sanitize(data['vimeo'], max_len=200),
        'thumb': sanitize(data['thumb'], max_len=300),
        'title': sanitize(data['title'], max_len=200),
        'desc':  sanitize(data['desc'],  max_len=1000),
        'tags':  [sanitize(t, max_len=50) for t in data.get('tags', []) if t][:10],
        'link':  sanitize(data.get('link', ''), max_len=300),
    })
    return jsonify({'status': 'added'})

@app.route('/api/admin/work/<work_id>', methods=['PUT'])
@login_required
def update_work(work_id):
    if work_col is None:
        return jsonify({'error': 'DB unavailable'}), 500
    oid = safe_object_id(work_id)
    if not oid:
        return jsonify({'error': 'Invalid id'}), 400
    data    = request.json or {}
    allowed = {'vimeo', 'thumb', 'title', 'desc', 'tags', 'link', 'num'}
    update  = {k: v for k, v in data.items() if k in allowed}
    if not update:
        return jsonify({'error': 'Nothing to update'}), 400
    work_col.update_one({'_id': oid}, {'$set': update})
    return jsonify({'status': 'updated'})

@app.route('/api/admin/work/<work_id>', methods=['DELETE'])
@login_required
def delete_work(work_id):
    if work_col is None:
        return jsonify({'error': 'DB unavailable'}), 500
    oid = safe_object_id(work_id)
    if not oid:
        return jsonify({'error': 'Invalid id'}), 400
    work_col.delete_one({'_id': oid})
    return jsonify({'status': 'deleted'})

# ── CONTACT FORM ──────────────────────────────────────────────────────────────
@app.route('/api/contact', methods=['POST'])
@limiter.limit('3 per hour')
def save_message():
    if messages_col is None:
        return jsonify({'error': 'DB unavailable'}), 500
    data    = request.json or {}
    name    = sanitize(data.get('name')    or '', max_len=100)
    email   = sanitize(data.get('email')   or '', max_len=200)
    message = sanitize(data.get('message') or '', max_len=2000)
    if not name or not email or not message:
        return jsonify({'error': 'All fields required'}), 400
    messages_col.insert_one({
        'name': name, 'email': email, 'message': message,
        'read': False, 'date': datetime.now(timezone.utc)
    })
    return jsonify({'status': 'sent'})

@app.route('/api/admin/messages')
@login_required
def get_messages():
    if messages_col is None:
        return jsonify([]), 500
    msgs = list(messages_col.find({}).sort('date', -1))
    for m in msgs:
        m['_id']  = str(m['_id'])
        m['date'] = m['date'].strftime('%d %b %Y, %H:%M') if m.get('date') else ''
    return jsonify(msgs)

@app.route('/api/admin/messages/<msg_id>/read', methods=['POST'])
@login_required
def mark_read(msg_id):
    if messages_col is None:
        return jsonify({}), 500
    oid = safe_object_id(msg_id)
    if not oid:
        return jsonify({'error': 'Invalid id'}), 400
    messages_col.update_one({'_id': oid}, {'$set': {'read': True}})
    return jsonify({'status': 'ok'})

@app.route('/api/admin/messages/<msg_id>', methods=['DELETE'])
@login_required
def delete_message(msg_id):
    if messages_col is None:
        return jsonify({}), 500
    oid = safe_object_id(msg_id)
    if not oid:
        return jsonify({'error': 'Invalid id'}), 400
    messages_col.delete_one({'_id': oid})
    return jsonify({'status': 'deleted'})

# ── REORDER — CREDITS ─────────────────────────────────────────────────────────
@app.route('/api/admin/credits/reorder', methods=['POST'])
@login_required
def reorder_credits():
    if credits_col is None:
        return jsonify({'error': 'DB unavailable'}), 500
    order = (request.json or {}).get('order', [])
    for item in order:
        oid = safe_object_id(item.get('id'))
        if oid:
            credits_col.update_one({'_id': oid}, {'$set': {'order': item['order']}})
    return jsonify({'status': 'reordered'})

# ── SKILLS API ───────────────────────────────────────────────────────────────
@app.route('/api/skills')
def get_skills():
    if skills_col is None:
        return jsonify([]), 500
    items = list(skills_col.find({}).sort('order', 1))
    for i in items:
        i['_id'] = str(i['_id'])
    return jsonify(items)

@app.route('/api/admin/skills', methods=['POST'])
@login_required
def add_skill():
    if skills_col is None:
        return jsonify({'error': 'DB unavailable'}), 500
    data  = request.json or {}
    name  = sanitize(data.get('name') or '', max_len=60)
    level = max(0, min(100, int(data.get('level', 80))))
    if not name:
        return jsonify({'error': 'name required'}), 400
    top   = skills_col.find_one(sort=[('order', -1)])
    order = (top['order'] + 1) if top else 0
    result = skills_col.insert_one({'name': name, 'level': level, 'order': order})
    return jsonify({'status': 'added', '_id': str(result.inserted_id)})

@app.route('/api/admin/skills/<skill_id>', methods=['PUT'])
@login_required
def update_skill(skill_id):
    if skills_col is None:
        return jsonify({'error': 'DB unavailable'}), 500
    oid  = safe_object_id(skill_id)
    if not oid:
        return jsonify({'error': 'Invalid id'}), 400
    data  = request.json or {}
    name  = sanitize(data.get('name') or '', max_len=60)
    level = max(0, min(100, int(data.get('level', 80))))
    if not name:
        return jsonify({'error': 'name required'}), 400
    skills_col.update_one({'_id': oid}, {'$set': {'name': name, 'level': level}})
    return jsonify({'status': 'updated'})

@app.route('/api/admin/skills/<skill_id>', methods=['DELETE'])
@login_required
def delete_skill(skill_id):
    if skills_col is None:
        return jsonify({'error': 'DB unavailable'}), 500
    oid = safe_object_id(skill_id)
    if not oid:
        return jsonify({'error': 'Invalid id'}), 400
    skills_col.delete_one({'_id': oid})
    return jsonify({'status': 'deleted'})

@app.route('/api/admin/available', methods=['POST'])
@login_required
def set_available():
    if about_col is None:
        return jsonify({'error': 'DB unavailable'}), 500
    val = bool((request.json or {}).get('available', False))
    about_col.update_one({'_id': 'about'}, {'$set': {'available': val}}, upsert=True)
    return jsonify({'status': 'updated', 'available': val})

@app.route('/api/admin/theme', methods=['POST'])
@login_required
def set_theme():
    if about_col is None:
        return jsonify({'error': 'DB unavailable'}), 500
    theme = 'day' if (request.json or {}).get('day') else 'dark'
    about_col.update_one({'_id': 'about'}, {'$set': {'theme': theme}}, upsert=True)
    return jsonify({'status': 'updated', 'theme': theme})

@app.route('/api/weather')
def get_weather():
    if about_col is None:
        return jsonify({'error': 'DB unavailable'}), 500
    doc = about_col.find_one({'_id': 'about'}, {'location': 1}) or {}
    loc = doc.get('location', {})
    lat, lon = loc.get('lat'), loc.get('lon')
    city = loc.get('city', '')
    if not lat or not lon:
        return jsonify({'error': 'no location set'}), 404
    return jsonify({'city': city, 'lat': lat, 'lon': lon})

# ── TIMELINE API ─────────────────────────────────────────────────────────────
@app.route('/api/timeline')
def get_timeline():
    if timeline_col is None:
        return jsonify([]), 500
    items = list(timeline_col.find({}).sort('order', 1))
    for i in items:
        i['_id'] = str(i['_id'])
    return jsonify(items)

@app.route('/api/admin/timeline', methods=['POST'])
@login_required
def add_timeline():
    if timeline_col is None:
        return jsonify({'error': 'DB unavailable'}), 500
    data  = request.json or {}
    role  = sanitize(data.get('role')    or '', max_len=200)
    org   = sanitize(data.get('org')     or '', max_len=200)
    period= sanitize(data.get('period')  or '', max_len=50)
    desc  = sanitize(data.get('desc')    or '', max_len=500)
    tags  = [sanitize(t, max_len=50) for t in data.get('tags', []) if t][:8]
    if not role or not org:
        return jsonify({'error': 'role and org required'}), 400
    top   = timeline_col.find_one(sort=[('order', -1)])
    order = (top['order'] + 1) if top else 0
    result = timeline_col.insert_one({'role': role, 'org': org, 'period': period, 'desc': desc, 'tags': tags, 'order': order})
    return jsonify({'status': 'added', '_id': str(result.inserted_id)})

@app.route('/api/admin/timeline/<item_id>', methods=['PUT'])
@login_required
def update_timeline(item_id):
    if timeline_col is None:
        return jsonify({'error': 'DB unavailable'}), 500
    oid = safe_object_id(item_id)
    if not oid:
        return jsonify({'error': 'Invalid id'}), 400
    data = request.json or {}
    timeline_col.update_one({'_id': oid}, {'$set': {
        'role':   sanitize(data.get('role')   or '', max_len=200),
        'org':    sanitize(data.get('org')    or '', max_len=200),
        'period': sanitize(data.get('period') or '', max_len=50),
        'desc':   sanitize(data.get('desc')   or '', max_len=500),
        'tags':   [sanitize(t, max_len=50) for t in data.get('tags', []) if t][:8],
    }})
    return jsonify({'status': 'updated'})

@app.route('/api/admin/timeline/<item_id>', methods=['DELETE'])
@login_required
def delete_timeline(item_id):
    if timeline_col is None:
        return jsonify({'error': 'DB unavailable'}), 500
    oid = safe_object_id(item_id)
    if not oid:
        return jsonify({'error': 'Invalid id'}), 400
    timeline_col.delete_one({'_id': oid})
    return jsonify({'status': 'deleted'})

@app.route('/api/admin/timeline/reorder', methods=['POST'])
@login_required
def reorder_timeline():
    if timeline_col is None:
        return jsonify({'error': 'DB unavailable'}), 500
    order = (request.json or {}).get('order', [])
    for item in order:
        oid = safe_object_id(item.get('id'))
        if oid:
            timeline_col.update_one({'_id': oid}, {'$set': {'order': item['order']}})
    return jsonify({'status': 'reordered'})

# ── AWARDS API ───────────────────────────────────────────────────────────────
@app.route('/api/awards')
def get_awards():
    if awards_col is None:
        return jsonify([]), 500
    items = list(awards_col.find({}).sort('order', 1))
    for i in items:
        i['_id'] = str(i['_id'])
    return jsonify(items)

@app.route('/api/admin/awards', methods=['POST'])
@login_required
def add_award():
    if awards_col is None:
        return jsonify({'error': 'DB unavailable'}), 500
    data  = request.json or {}
    title = sanitize(data.get('title') or '', max_len=200)
    org   = sanitize(data.get('org')   or '', max_len=200)
    year  = sanitize(data.get('year')  or '', max_len=10)
    desc  = sanitize(data.get('desc')  or '', max_len=500)
    if not title:
        return jsonify({'error': 'title required'}), 400
    top   = awards_col.find_one(sort=[('order', -1)])
    order = (top['order'] + 1) if top else 0
    result = awards_col.insert_one({'title': title, 'org': org, 'year': year, 'desc': desc, 'order': order})
    return jsonify({'status': 'added', '_id': str(result.inserted_id)})

@app.route('/api/admin/awards/<award_id>', methods=['PUT'])
@login_required
def update_award(award_id):
    if awards_col is None:
        return jsonify({'error': 'DB unavailable'}), 500
    oid = safe_object_id(award_id)
    if not oid:
        return jsonify({'error': 'Invalid id'}), 400
    data = request.json or {}
    awards_col.update_one({'_id': oid}, {'$set': {
        'title': sanitize(data.get('title') or '', max_len=200),
        'org':   sanitize(data.get('org')   or '', max_len=200),
        'year':  sanitize(data.get('year')  or '', max_len=10),
        'desc':  sanitize(data.get('desc')  or '', max_len=500),
    }})
    return jsonify({'status': 'updated'})

@app.route('/api/admin/awards/<award_id>', methods=['DELETE'])
@login_required
def delete_award(award_id):
    if awards_col is None:
        return jsonify({'error': 'DB unavailable'}), 500
    oid = safe_object_id(award_id)
    if not oid:
        return jsonify({'error': 'Invalid id'}), 400
    awards_col.delete_one({'_id': oid})
    return jsonify({'status': 'deleted'})

# ── BLOGS API ─────────────────────────────────────────────────────────────────
@app.route('/api/blogs')
def get_blogs():
    if blogs_col is None:
        return jsonify([]), 500
    items = list(blogs_col.find({}).sort('date', -1))
    for i in items:
        i['_id']  = str(i['_id'])
        i['date'] = i['date'].strftime('%d %b %Y') if i.get('date') else ''
    return jsonify(items)

@app.route('/api/admin/blogs', methods=['POST'])
@login_required
def add_blog():
    if blogs_col is None:
        return jsonify({'error': 'DB unavailable'}), 500
    data    = request.json or {}
    title   = sanitize(data.get('title')   or '', max_len=200)
    excerpt = sanitize(data.get('excerpt') or '', max_len=400)
    body    = sanitize(data.get('body')    or '', max_len=5000)
    thumb   = sanitize(data.get('thumb')   or '', max_len=300)
    tags    = [sanitize(t, max_len=50) for t in data.get('tags', []) if t][:8]
    if not title or not body:
        return jsonify({'error': 'title and body required'}), 400
    result = blogs_col.insert_one({
        'title': title, 'excerpt': excerpt, 'body': body,
        'thumb': thumb, 'tags': tags, 'date': datetime.now(timezone.utc)
    })
    return jsonify({'status': 'added', '_id': str(result.inserted_id)})

@app.route('/api/admin/blogs/<blog_id>', methods=['PUT'])
@login_required
def update_blog(blog_id):
    if blogs_col is None:
        return jsonify({'error': 'DB unavailable'}), 500
    oid = safe_object_id(blog_id)
    if not oid:
        return jsonify({'error': 'Invalid id'}), 400
    data = request.json or {}
    blogs_col.update_one({'_id': oid}, {'$set': {
        'title':   sanitize(data.get('title')   or '', max_len=200),
        'excerpt': sanitize(data.get('excerpt') or '', max_len=400),
        'body':    sanitize(data.get('body')    or '', max_len=5000),
        'thumb':   sanitize(data.get('thumb')   or '', max_len=300),
        'tags':    [sanitize(t, max_len=50) for t in data.get('tags', []) if t][:8],
    }})
    return jsonify({'status': 'updated'})

@app.route('/api/admin/blogs/<blog_id>', methods=['DELETE'])
@login_required
def delete_blog(blog_id):
    if blogs_col is None:
        return jsonify({'error': 'DB unavailable'}), 500
    oid = safe_object_id(blog_id)
    if not oid:
        return jsonify({'error': 'Invalid id'}), 400
    blogs_col.delete_one({'_id': oid})
    return jsonify({'status': 'deleted'})

# ── PUBLIC READ APIs ──────────────────────────────────────────────────────────
@app.route('/api/about')
def get_about():
    if about_col is None:
        return jsonify({}), 500
    doc = about_col.find_one({'_id': 'about'}, {'_id': 0})
    return jsonify(doc or {})

@app.route('/api/credits')
def get_credits():
    if credits_col is None:
        return jsonify([]), 500
    cats = list(credits_col.find({}, {'_id': 1, 'category': 1, 'order': 1, 'videos': 1}).sort('order', 1))
    for c in cats:
        c['_id'] = str(c['_id'])
    return jsonify(cats)

@app.route('/api/work')
def get_work():
    if work_col is None:
        return jsonify([]), 500
    items = list(work_col.find(
        {}, {'_id': 1, 'order': 1, 'num': 1, 'vimeo': 1, 'thumb': 1,
             'title': 1, 'desc': 1, 'tags': 1, 'link': 1, 'views': 1}
    ).sort('order', 1))
    for i in items:
        i['_id'] = str(i['_id'])
        i.setdefault('views', 0)
    return jsonify(items)

# ── COMPANIES API ─────────────────────────────────────────────────────────────
@app.route('/api/companies')
def get_companies():
    """Public endpoint to get all companies for footer display"""
    if companies_col is None:
        return jsonify([]), 500
    companies = list(companies_col.find({}).sort('order', 1))
    for c in companies:
        c['_id'] = str(c['_id'])
        if 'created_at' in c:
            c['created_at'] = c['created_at'].isoformat() if c['created_at'] else None
    return jsonify(companies)

@app.route('/api/admin/companies', methods=['GET'])
@login_required
def admin_get_companies():
    """Admin endpoint to get all companies"""
    if companies_col is None:
        return jsonify([]), 500
    companies = list(companies_col.find({}).sort('order', 1))
    for c in companies:
        c['_id'] = str(c['_id'])
        if 'created_at' in c:
            c['created_at'] = c['created_at'].isoformat() if c['created_at'] else None
    return jsonify(companies)

@app.route('/api/admin/companies', methods=['POST'])
@login_required
def add_company():
    """Add a new company"""
    if companies_col is None:
        return jsonify({'error': 'DB unavailable'}), 500
    
    data = request.json or {}
    name = sanitize(data.get('name', ''), max_len=100)
    img_url = sanitize(data.get('img_url', ''), max_len=500)
    
    if not name or not img_url:
        return jsonify({'error': 'Both name and image URL are required'}), 400
    
    # Get the highest order value
    last_company = companies_col.find_one(sort=[('order', -1)])
    order = (last_company.get('order', -1) + 1) if last_company else 0
    
    result = companies_col.insert_one({
        'name': name,
        'img_url': img_url,
        'order': order,
        'created_at': datetime.now(timezone.utc)
    })
    
    return jsonify({
        'status': 'added',
        '_id': str(result.inserted_id),
        'name': name,
        'img_url': img_url,
        'order': order
    })

@app.route('/api/admin/companies/<company_id>', methods=['PUT'])
@login_required
def update_company(company_id):
    """Update a company"""
    if companies_col is None:
        return jsonify({'error': 'DB unavailable'}), 500
    
    oid = safe_object_id(company_id)
    if not oid:
        return jsonify({'error': 'Invalid id'}), 400
    
    data = request.json or {}
    name = sanitize(data.get('name', ''), max_len=100)
    img_url = sanitize(data.get('img_url', ''), max_len=500)
    
    if not name and not img_url:
        return jsonify({'error': 'Nothing to update'}), 400
    
    update_data = {}
    if name:
        update_data['name'] = name
    if img_url:
        update_data['img_url'] = img_url
    
    companies_col.update_one({'_id': oid}, {'$set': update_data})
    return jsonify({'status': 'updated'})

@app.route('/api/admin/companies/<company_id>', methods=['DELETE'])
@login_required
def delete_company(company_id):
    """Delete a company"""
    if companies_col is None:
        return jsonify({'error': 'DB unavailable'}), 500
    
    oid = safe_object_id(company_id)
    if not oid:
        return jsonify({'error': 'Invalid id'}), 400
    
    companies_col.delete_one({'_id': oid})
    return jsonify({'status': 'deleted'})

@app.route('/api/admin/companies/reorder', methods=['POST'])
@login_required
def reorder_companies():
    if companies_col is None:
        return jsonify({'error': 'DB unavailable'}), 500
    order_data = (request.json or {}).get('order', [])
    for item in order_data:
        oid = safe_object_id(item.get('id'))
        if oid:
            companies_col.update_one({'_id': oid}, {'$set': {'order': item.get('order', 0)}})
    return jsonify({'status': 'reordered'})

# ── STILLS API ────────────────────────────────────────────────────────────────
@app.route('/api/stills')
def get_stills():
    if stills_col is None:
        return jsonify([]), 500
    items = list(stills_col.find({}).sort('order', 1))
    for i in items:
        i['_id'] = str(i['_id'])
    return jsonify(items)

@app.route('/api/admin/stills', methods=['POST'])
@login_required
def add_still():
    if stills_col is None:
        return jsonify({'error': 'DB unavailable'}), 500
    data    = request.json or {}
    url     = sanitize(data.get('url') or '', max_len=500)
    caption = sanitize(data.get('caption') or '', max_len=200)
    if not url:
        return jsonify({'error': 'url required'}), 400
    top   = stills_col.find_one(sort=[('order', -1)])
    order = (top['order'] + 1) if top else 0
    result = stills_col.insert_one({'url': url, 'caption': caption, 'order': order})
    return jsonify({'status': 'added', '_id': str(result.inserted_id)})

@app.route('/api/admin/stills/<still_id>', methods=['PUT'])
@login_required
def update_still(still_id):
    if stills_col is None:
        return jsonify({'error': 'DB unavailable'}), 500
    oid = safe_object_id(still_id)
    if not oid:
        return jsonify({'error': 'Invalid id'}), 400
    data = request.json or {}
    stills_col.update_one({'_id': oid}, {'$set': {
        'url':     sanitize(data.get('url') or '', max_len=500),
        'caption': sanitize(data.get('caption') or '', max_len=200),
    }})
    return jsonify({'status': 'updated'})

@app.route('/api/admin/stills/<still_id>', methods=['DELETE'])
@login_required
def delete_still(still_id):
    if stills_col is None:
        return jsonify({'error': 'DB unavailable'}), 500
    oid = safe_object_id(still_id)
    if not oid:
        return jsonify({'error': 'Invalid id'}), 400
    stills_col.delete_one({'_id': oid})
    return jsonify({'status': 'deleted'})

@app.route('/api/admin/stills/reorder', methods=['POST'])
@login_required
def reorder_stills():
    if stills_col is None:
        return jsonify({'error': 'DB unavailable'}), 500
    order = (request.json or {}).get('order', [])
    for item in order:
        oid = safe_object_id(item.get('id'))
        if oid:
            stills_col.update_one({'_id': oid}, {'$set': {'order': item['order']}})
    return jsonify({'status': 'reordered'})

# ── RUN ───────────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=os.environ.get('FLASK_DEBUG', 'false').lower() == 'true')
