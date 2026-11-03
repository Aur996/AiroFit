from flask import Flask, request, jsonify, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from datetime import datetime, date, timedelta
import os
import uuid
import json
import base64
import requests
import re

# 简单加载 .env 文件（避免硬编码密钥，也无需额外依赖）
def _load_env():
    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
    if not os.path.exists(env_path):
        return
    with open(env_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#') or '=' not in line:
                continue
            key, _, value = line.partition('=')
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = value

_load_env()

app = Flask(__name__)
CORS(app)

# 数据库配置 - 使用 SQLite
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///fitness.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'static', 'uploads')
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

db = SQLAlchemy(app)


class Post(db.Model):
    __tablename__ = 'posts'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, default=1)
    username = db.Column(db.String(50), default='匿名用户')
    content = db.Column(db.Text, nullable=False)
    image_urls = db.Column(db.Text, default='')
    like_count = db.Column(db.Integer, default=0)
    time = db.Column(db.DateTime, default=datetime.utcnow)


class Comment(db.Model):
    __tablename__ = 'comments'
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, nullable=False)
    user_id = db.Column(db.Integer, default=1)
    username = db.Column(db.String(50), default='匿名用户')
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Like(db.Model):
    __tablename__ = 'likes'
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, nullable=False)
    user_id = db.Column(db.Integer, default=1)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class FoodRecord(db.Model):
    __tablename__ = 'food_records'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, default=1)
    meal_type = db.Column(db.String(20), default='lunch')
    food_name = db.Column(db.String(100), nullable=False)
    food_name_cn = db.Column(db.String(100), default='')
    weight_g = db.Column(db.Float, default=200)
    calorie = db.Column(db.Float, default=0)
    protein = db.Column(db.Float, default=0)
    carb = db.Column(db.Float, default=0)
    fat = db.Column(db.Float, default=0)
    fiber = db.Column(db.Float, default=0)
    image_url = db.Column(db.String(500), default='')
    confidence = db.Column(db.Float, default=0.0)
    note = db.Column(db.Text, default='')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class DailySummary(db.Model):
    __tablename__ = 'daily_summaries'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, default=1)
    record_date = db.Column(db.Date, nullable=False)
    total_calorie = db.Column(db.Float, default=0)
    total_protein = db.Column(db.Float, default=0)
    total_carb = db.Column(db.Float, default=0)
    total_fat = db.Column(db.Float, default=0)
    meal_count = db.Column(db.Integer, default=0)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)


class UserProfile(db.Model):
    __tablename__ = 'user_profiles'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, default=1, unique=True)
    nickname = db.Column(db.String(50), default='健身达人')
    avatar = db.Column(db.String(255), default='')
    signature = db.Column(db.String(200), default='')
    contact = db.Column(db.String(100), default='')
    gender = db.Column(db.String(10), default='male')  # male / female
    age = db.Column(db.Integer, default=25)
    height_cm = db.Column(db.Float, default=170)
    weight_kg = db.Column(db.Float, default=65)
    activity_level = db.Column(db.String(20), default='light')  # sedentary/light/moderate/active/very_active
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ExerciseRecord(db.Model):
    __tablename__ = 'exercise_records'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, default=1)
    exercise_type = db.Column(db.String(50), nullable=False)
    duration_min = db.Column(db.Float, default=30)
    calorie_burn = db.Column(db.Float, default=0)
    record_date = db.Column(db.Date, default=date.today)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Product(db.Model):
    __tablename__ = 'products'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(30), default='器材')
    price = db.Column(db.Float, default=0)
    original_price = db.Column(db.Float, default=0)
    image = db.Column(db.String(255), default='')
    description = db.Column(db.Text, default='')
    stock = db.Column(db.Integer, default=100)
    sales = db.Column(db.Integer, default=0)


class Order(db.Model):
    __tablename__ = 'orders'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, default=1)
    items = db.Column(db.Text, default='')  # JSON 字符串
    total_price = db.Column(db.Float, default=0)
    status = db.Column(db.String(20), default='待发货')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


with app.app_context():
    db.create_all()
print("Database ready (SQLite)")


# ============ 食物营养数据库 (每100g) ============

FOOD_NUTRITION_DB = {
    "rice": {"name_cn": "米饭", "calorie": 116, "protein": 2.6, "carb": 25.9, "fat": 0.3, "fiber": 0.3},
    "brown_rice": {"name_cn": "糙米饭", "calorie": 123, "protein": 2.7, "carb": 25.6, "fat": 0.9, "fiber": 1.0},
    "noodles": {"name_cn": "面条", "calorie": 110, "protein": 3.3, "carb": 22.3, "fat": 0.4, "fiber": 0.5},
    "bread": {"name_cn": "面包", "calorie": 265, "protein": 8.5, "carb": 49.0, "fat": 3.2, "fiber": 2.4},
    "whole_wheat_bread": {"name_cn": "全麦面包", "calorie": 247, "protein": 9.0, "carb": 43.0, "fat": 3.4, "fiber": 6.0},
    "steamed_bun": {"name_cn": "馒头", "calorie": 223, "protein": 7.0, "carb": 44.2, "fat": 1.1, "fiber": 1.3},
    "dumpling": {"name_cn": "饺子", "calorie": 250, "protein": 9.0, "carb": 28.0, "fat": 10.0, "fiber": 1.0},
    "corn": {"name_cn": "玉米", "calorie": 112, "protein": 4.0, "carb": 22.8, "fat": 1.2, "fiber": 2.9},
    "sweet_potato": {"name_cn": "红薯", "calorie": 86, "protein": 1.6, "carb": 20.1, "fat": 0.1, "fiber": 3.0},
    "oatmeal": {"name_cn": "燕麦", "calorie": 377, "protein": 13.5, "carb": 66.3, "fat": 6.7, "fiber": 10.6},
    "chicken_breast": {"name_cn": "鸡胸肉", "calorie": 133, "protein": 31.0, "carb": 0, "fat": 1.2, "fiber": 0},
    "chicken": {"name_cn": "鸡肉", "calorie": 167, "protein": 19.3, "carb": 1.3, "fat": 9.4, "fiber": 0},
    "chicken_leg": {"name_cn": "鸡腿", "calorie": 181, "protein": 16.0, "carb": 0, "fat": 13.0, "fiber": 0},
    "beef": {"name_cn": "牛肉", "calorie": 125, "protein": 20.2, "carb": 1.2, "fat": 4.2, "fiber": 0},
    "steak": {"name_cn": "牛排", "calorie": 200, "protein": 26.0, "carb": 0, "fat": 10.0, "fiber": 0},
    "pork": {"name_cn": "猪肉", "calorie": 242, "protein": 13.2, "carb": 0, "fat": 20.8, "fiber": 0},
    "lean_pork": {"name_cn": "瘦猪肉", "calorie": 143, "protein": 20.3, "carb": 1.5, "fat": 6.2, "fiber": 0},
    "lamb": {"name_cn": "羊肉", "calorie": 203, "protein": 19.0, "carb": 0, "fat": 14.1, "fiber": 0},
    "duck": {"name_cn": "鸭肉", "calorie": 240, "protein": 15.5, "carb": 0.5, "fat": 19.7, "fiber": 0},
    "fish": {"name_cn": "鱼肉", "calorie": 104, "protein": 17.6, "carb": 0, "fat": 3.4, "fiber": 0},
    "salmon": {"name_cn": "三文鱼", "calorie": 208, "protein": 20.4, "carb": 0, "fat": 13.4, "fiber": 0},
    "shrimp": {"name_cn": "虾", "calorie": 99, "protein": 20.3, "carb": 0.2, "fat": 1.0, "fiber": 0},
    "crab": {"name_cn": "螃蟹", "calorie": 95, "protein": 13.8, "carb": 2.3, "fat": 2.6, "fiber": 0},
    "squid": {"name_cn": "鱿鱼", "calorie": 92, "protein": 17.4, "carb": 1.6, "fat": 1.6, "fiber": 0},
    "egg": {"name_cn": "鸡蛋", "calorie": 144, "protein": 13.3, "carb": 1.5, "fat": 9.5, "fiber": 0},
    "egg_white": {"name_cn": "蛋白", "calorie": 48, "protein": 11.0, "carb": 0.7, "fat": 0.1, "fiber": 0},
    "milk": {"name_cn": "牛奶", "calorie": 54, "protein": 3.0, "carb": 4.9, "fat": 2.5, "fiber": 0},
    "yogurt": {"name_cn": "酸奶", "calorie": 72, "protein": 3.5, "carb": 9.3, "fat": 2.1, "fiber": 0},
    "cheese": {"name_cn": "奶酪", "calorie": 328, "protein": 25.7, "carb": 1.3, "fat": 23.5, "fiber": 0},
    "broccoli": {"name_cn": "西兰花", "calorie": 34, "protein": 2.8, "carb": 6.6, "fat": 0.4, "fiber": 2.6},
    "spinach": {"name_cn": "菠菜", "calorie": 23, "protein": 2.9, "carb": 3.6, "fat": 0.4, "fiber": 2.2},
    "tomato": {"name_cn": "番茄", "calorie": 18, "protein": 0.9, "carb": 3.9, "fat": 0.2, "fiber": 1.2},
    "cucumber": {"name_cn": "黄瓜", "calorie": 15, "protein": 0.7, "carb": 2.9, "fat": 0.1, "fiber": 0.5},
    "carrot": {"name_cn": "胡萝卜", "calorie": 41, "protein": 0.9, "carb": 9.6, "fat": 0.2, "fiber": 2.8},
    "lettuce": {"name_cn": "生菜", "calorie": 15, "protein": 1.4, "carb": 2.8, "fat": 0.2, "fiber": 1.3},
    "cabbage": {"name_cn": "卷心菜", "calorie": 25, "protein": 1.3, "carb": 5.8, "fat": 0.1, "fiber": 2.5},
    "celery": {"name_cn": "芹菜", "calorie": 16, "protein": 0.7, "carb": 3.3, "fat": 0.1, "fiber": 1.6},
    "bell_pepper": {"name_cn": "彩椒", "calorie": 20, "protein": 0.9, "carb": 4.6, "fat": 0.2, "fiber": 1.7},
    "mushroom": {"name_cn": "蘑菇", "calorie": 22, "protein": 3.1, "carb": 3.3, "fat": 0.3, "fiber": 1.0},
    "potato": {"name_cn": "土豆", "calorie": 77, "protein": 2.0, "carb": 17.5, "fat": 0.1, "fiber": 2.2},
    "tofu": {"name_cn": "豆腐", "calorie": 76, "protein": 8.1, "carb": 1.9, "fat": 3.7, "fiber": 0.3},
    "apple": {"name_cn": "苹果", "calorie": 52, "protein": 0.3, "carb": 14.0, "fat": 0.2, "fiber": 2.4},
    "banana": {"name_cn": "香蕉", "calorie": 89, "protein": 1.1, "carb": 22.8, "fat": 0.3, "fiber": 2.6},
    "orange": {"name_cn": "橙子", "calorie": 47, "protein": 0.9, "carb": 11.8, "fat": 0.1, "fiber": 2.4},
    "grape": {"name_cn": "葡萄", "calorie": 69, "protein": 0.7, "carb": 18.1, "fat": 0.2, "fiber": 0.9},
    "watermelon": {"name_cn": "西瓜", "calorie": 30, "protein": 0.6, "carb": 7.6, "fat": 0.2, "fiber": 0.4},
    "strawberry": {"name_cn": "草莓", "calorie": 32, "protein": 0.7, "carb": 7.7, "fat": 0.3, "fiber": 2.0},
    "blueberry": {"name_cn": "蓝莓", "calorie": 57, "protein": 0.7, "carb": 14.5, "fat": 0.3, "fiber": 2.4},
    "avocado": {"name_cn": "牛油果", "calorie": 160, "protein": 2.0, "carb": 8.5, "fat": 14.7, "fiber": 6.7},
    "kiwi": {"name_cn": "猕猴桃", "calorie": 61, "protein": 1.1, "carb": 14.7, "fat": 0.5, "fiber": 3.0},
    "pineapple": {"name_cn": "菠萝", "calorie": 50, "protein": 0.5, "carb": 13.1, "fat": 0.1, "fiber": 1.4},
    "almond": {"name_cn": "杏仁", "calorie": 579, "protein": 21.2, "carb": 21.6, "fat": 49.9, "fiber": 12.5},
    "walnut": {"name_cn": "核桃", "calorie": 654, "protein": 15.2, "carb": 13.7, "fat": 65.2, "fiber": 6.7},
    "peanut": {"name_cn": "花生", "calorie": 567, "protein": 25.8, "carb": 16.1, "fat": 49.2, "fiber": 8.5},
    "cashew": {"name_cn": "腰果", "calorie": 553, "protein": 18.2, "carb": 30.2, "fat": 43.9, "fiber": 3.3},
    "coffee": {"name_cn": "咖啡", "calorie": 2, "protein": 0.1, "carb": 0, "fat": 0, "fiber": 0},
    "green_tea": {"name_cn": "绿茶", "calorie": 1, "protein": 0, "carb": 0.2, "fat": 0, "fiber": 0},
    "orange_juice": {"name_cn": "橙汁", "calorie": 45, "protein": 0.7, "carb": 10.4, "fat": 0.2, "fiber": 0.2},
    "cola": {"name_cn": "可乐", "calorie": 42, "protein": 0, "carb": 10.6, "fat": 0, "fiber": 0},
    "soy_milk": {"name_cn": "豆浆", "calorie": 33, "protein": 2.9, "carb": 1.8, "fat": 1.5, "fiber": 0.4},
    "kung_pao_chicken": {"name_cn": "宫保鸡丁", "calorie": 180, "protein": 16.0, "carb": 8.0, "fat": 9.0, "fiber": 1.0},
    "mapo_tofu": {"name_cn": "麻婆豆腐", "calorie": 120, "protein": 8.0, "carb": 5.0, "fat": 7.0, "fiber": 1.0},
    "sweet_sour_pork": {"name_cn": "糖醋里脊", "calorie": 220, "protein": 12.0, "carb": 18.0, "fat": 11.0, "fiber": 0.5},
    "fried_rice": {"name_cn": "炒饭", "calorie": 180, "protein": 5.5, "carb": 28.0, "fat": 5.0, "fiber": 0.8},
    "hotpot": {"name_cn": "火锅", "calorie": 150, "protein": 10.0, "carb": 5.0, "fat": 9.0, "fiber": 1.5},
    "salad": {"name_cn": "沙拉", "calorie": 45, "protein": 1.5, "carb": 5.0, "fat": 2.0, "fiber": 2.0},
    "sushi": {"name_cn": "寿司", "calorie": 145, "protein": 6.0, "carb": 26.0, "fat": 1.5, "fiber": 0.5},
    "pizza": {"name_cn": "披萨", "calorie": 266, "protein": 11.4, "carb": 33.0, "fat": 10.0, "fiber": 2.3},
    "hamburger": {"name_cn": "汉堡", "calorie": 295, "protein": 17.0, "carb": 30.0, "fat": 12.0, "fiber": 1.5},
    "sandwich": {"name_cn": "三明治", "calorie": 250, "protein": 12.0, "carb": 28.0, "fat": 9.0, "fiber": 2.0},
    "pasta": {"name_cn": "意面", "calorie": 131, "protein": 5.0, "carb": 25.0, "fat": 1.1, "fiber": 1.8},
    "porridge": {"name_cn": "粥", "calorie": 46, "protein": 1.1, "carb": 9.8, "fat": 0.3, "fiber": 0.3},
    "congee": {"name_cn": "白粥", "calorie": 46, "protein": 1.1, "carb": 9.8, "fat": 0.3, "fiber": 0.3},
    "millet_porridge": {"name_cn": "小米粥", "calorie": 46, "protein": 1.4, "carb": 8.4, "fat": 0.7, "fiber": 0.8},
    "wonton": {"name_cn": "馄饨", "calorie": 170, "protein": 8.0, "carb": 22.0, "fat": 5.0, "fiber": 0.8},
    "baozi": {"name_cn": "包子", "calorie": 227, "protein": 8.0, "carb": 33.0, "fat": 6.0, "fiber": 1.2},
    "spring_roll": {"name_cn": "春卷", "calorie": 300, "protein": 6.0, "carb": 30.0, "fat": 18.0, "fiber": 1.5},
    "rice_noodle": {"name_cn": "米粉", "calorie": 109, "protein": 2.0, "carb": 24.0, "fat": 0.3, "fiber": 0.6},
    "udon": {"name_cn": "乌冬面", "calorie": 127, "protein": 3.5, "carb": 26.0, "fat": 0.5, "fiber": 1.0},
    "ramen": {"name_cn": "拉面", "calorie": 110, "protein": 4.0, "carb": 20.0, "fat": 2.0, "fiber": 1.0},
    "fried_noodles": {"name_cn": "炒面", "calorie": 200, "protein": 6.0, "carb": 28.0, "fat": 7.0, "fiber": 1.0},
    "braised_pork": {"name_cn": "红烧肉", "calorie": 478, "protein": 9.0, "carb": 3.0, "fat": 47.0, "fiber": 0},
    "twice_cooked_pork": {"name_cn": "回锅肉", "calorie": 240, "protein": 12.0, "carb": 5.0, "fat": 19.0, "fiber": 1.0},
    "spicy_chicken": {"name_cn": "辣子鸡", "calorie": 260, "protein": 18.0, "carb": 6.0, "fat": 18.0, "fiber": 1.0},
    "sweet_sour_chicken": {"name_cn": "糖醋鸡丁", "calorie": 210, "protein": 15.0, "carb": 15.0, "fat": 9.0, "fiber": 1.0},
    "beef_broccoli": {"name_cn": "西兰花炒牛肉", "calorie": 130, "protein": 12.0, "carb": 5.0, "fat": 7.0, "fiber": 1.5},
    "beef_noodles": {"name_cn": "牛肉面", "calorie": 120, "protein": 7.0, "carb": 16.0, "fat": 3.0, "fiber": 1.0},
    "fish_fragrant_pork": {"name_cn": "鱼香肉丝", "calorie": 190, "protein": 11.0, "carb": 10.0, "fat": 12.0, "fiber": 1.0},
    "scrambled_egg_tomato": {"name_cn": "番茄炒蛋", "calorie": 120, "protein": 6.0, "carb": 5.0, "fat": 8.0, "fiber": 1.0},
    "stir_fried_greens": {"name_cn": "炒青菜", "calorie": 60, "protein": 2.0, "carb": 5.0, "fat": 4.0, "fiber": 2.0},
    "eggplant": {"name_cn": "茄子", "calorie": 25, "protein": 1.0, "carb": 5.9, "fat": 0.2, "fiber": 3.0},
    "bok_choy": {"name_cn": "小白菜", "calorie": 15, "protein": 1.5, "carb": 2.3, "fat": 0.3, "fiber": 1.1},
    "cauliflower": {"name_cn": "花菜", "calorie": 25, "protein": 1.9, "carb": 5.0, "fat": 0.3, "fiber": 2.0},
    "green_bean": {"name_cn": "四季豆", "calorie": 31, "protein": 1.8, "carb": 7.0, "fat": 0.2, "fiber": 2.7},
    "onion": {"name_cn": "洋葱", "calorie": 40, "protein": 1.1, "carb": 9.3, "fat": 0.1, "fiber": 1.7},
    "garlic": {"name_cn": "大蒜", "calorie": 149, "protein": 6.4, "carb": 33.0, "fat": 0.5, "fiber": 2.1},
    "ginger": {"name_cn": "生姜", "calorie": 80, "protein": 1.8, "carb": 17.8, "fat": 0.8, "fiber": 2.0},
    "pumpkin": {"name_cn": "南瓜", "calorie": 26, "protein": 1.0, "carb": 6.5, "fat": 0.1, "fiber": 0.5},
    "lotus_root": {"name_cn": "莲藕", "calorie": 74, "protein": 1.9, "carb": 17.2, "fat": 0.1, "fiber": 2.2},
    "bamboo_shoot": {"name_cn": "竹笋", "calorie": 27, "protein": 2.6, "carb": 5.2, "fat": 0.3, "fiber": 2.2},
    "pear": {"name_cn": "梨", "calorie": 57, "protein": 0.4, "carb": 15.2, "fat": 0.1, "fiber": 3.1},
    "peach": {"name_cn": "桃子", "calorie": 39, "protein": 0.9, "carb": 9.5, "fat": 0.3, "fiber": 1.5},
    "mango": {"name_cn": "芒果", "calorie": 60, "protein": 0.8, "carb": 15.0, "fat": 0.4, "fiber": 1.6},
    "cherry": {"name_cn": "樱桃", "calorie": 63, "protein": 1.1, "carb": 16.0, "fat": 0.2, "fiber": 2.1},
    "dragon_fruit": {"name_cn": "火龙果", "calorie": 60, "protein": 1.1, "carb": 13.0, "fat": 0.3, "fiber": 2.9},
    "durian": {"name_cn": "榴莲", "calorie": 147, "protein": 1.5, "carb": 27.0, "fat": 5.3, "fiber": 3.8},
    "lychee": {"name_cn": "荔枝", "calorie": 66, "protein": 0.8, "carb": 16.5, "fat": 0.4, "fiber": 1.3},
    "coconut": {"name_cn": "椰子", "calorie": 354, "protein": 3.3, "carb": 15.2, "fat": 33.5, "fiber": 9.0},
    "pomelo": {"name_cn": "柚子", "calorie": 42, "protein": 0.8, "carb": 10.0, "fat": 0.1, "fiber": 1.0},
    "pistachio": {"name_cn": "开心果", "calorie": 562, "protein": 20.2, "carb": 27.2, "fat": 45.3, "fiber": 10.6},
    "sunflower_seed": {"name_cn": "瓜子", "calorie": 584, "protein": 20.8, "carb": 20.0, "fat": 51.5, "fiber": 8.6},
    "milk_tea": {"name_cn": "奶茶", "calorie": 80, "protein": 1.0, "carb": 11.0, "fat": 3.0, "fiber": 0},
    "beer": {"name_cn": "啤酒", "calorie": 43, "protein": 0.5, "carb": 3.6, "fat": 0, "fiber": 0},
    "red_wine": {"name_cn": "红酒", "calorie": 85, "protein": 0.1, "carb": 2.6, "fat": 0, "fiber": 0},
    "rice_wine": {"name_cn": "米酒", "calorie": 100, "protein": 1.0, "carb": 8.0, "fat": 0, "fiber": 0},
    "coconut_milk": {"name_cn": "椰汁", "calorie": 51, "protein": 0.4, "carb": 5.0, "fat": 2.0, "fiber": 0},
    "lemon_water": {"name_cn": "柠檬水", "calorie": 20, "protein": 0.1, "carb": 5.0, "fat": 0, "fiber": 0},
    "fried_chicken": {"name_cn": "炸鸡", "calorie": 280, "protein": 18.0, "carb": 10.0, "fat": 19.0, "fiber": 0.5},
    "fries": {"name_cn": "薯条", "calorie": 312, "protein": 3.4, "carb": 41.0, "fat": 15.0, "fiber": 3.8},
    "cake": {"name_cn": "蛋糕", "calorie": 347, "protein": 5.0, "carb": 50.0, "fat": 15.0, "fiber": 1.0},
    "cookie": {"name_cn": "饼干", "calorie": 435, "protein": 6.0, "carb": 71.0, "fat": 15.0, "fiber": 2.0},
    "chocolate": {"name_cn": "巧克力", "calorie": 546, "protein": 4.9, "carb": 59.0, "fat": 30.0, "fiber": 7.0},
    "ice_cream": {"name_cn": "冰淇淋", "calorie": 207, "protein": 3.5, "carb": 24.0, "fat": 11.0, "fiber": 0.7},
    "potato_chips": {"name_cn": "薯片", "calorie": 536, "protein": 6.0, "carb": 53.0, "fat": 34.0, "fiber": 4.0},
    "instant_noodles": {"name_cn": "方便面", "calorie": 473, "protein": 9.0, "carb": 61.0, "fat": 21.0, "fiber": 3.0},
    "toast": {"name_cn": "吐司", "calorie": 265, "protein": 8.5, "carb": 49.0, "fat": 3.2, "fiber": 2.4},
    "croissant": {"name_cn": "牛角包", "calorie": 406, "protein": 8.0, "carb": 45.0, "fat": 21.0, "fiber": 2.0},
    "steamed_egg": {"name_cn": "蒸蛋", "calorie": 60, "protein": 5.0, "carb": 1.0, "fat": 4.0, "fiber": 0},
    "tea_egg": {"name_cn": "茶叶蛋", "calorie": 144, "protein": 13.0, "carb": 1.5, "fat": 9.5, "fiber": 0},
    "sausage": {"name_cn": "香肠", "calorie": 300, "protein": 13.0, "carb": 2.0, "fat": 27.0, "fiber": 0},
    "bacon": {"name_cn": "培根", "calorie": 458, "protein": 30.0, "carb": 1.5, "fat": 35.0, "fiber": 0},
    "ham": {"name_cn": "火腿", "calorie": 145, "protein": 16.0, "carb": 1.0, "fat": 8.0, "fiber": 0},
}

CATEGORY_MAP = {
    "staple": ["rice", "brown_rice", "noodles", "bread", "whole_wheat_bread", "steamed_bun", "dumpling", "corn", "sweet_potato", "oatmeal", "fried_rice", "pasta", "porridge", "congee", "millet_porridge", "wonton", "baozi", "spring_roll", "rice_noodle", "udon", "ramen", "fried_noodles", "beef_noodles", "toast", "croissant", "instant_noodles"],
    "meat": ["chicken_breast", "chicken", "chicken_leg", "beef", "steak", "pork", "lean_pork", "lamb", "duck", "braised_pork", "twice_cooked_pork", "spicy_chicken", "sweet_sour_chicken", "beef_broccoli", "fish_fragrant_pork", "fried_chicken", "sausage", "bacon", "ham"],
    "seafood": ["fish", "salmon", "shrimp", "crab", "squid"],
    "egg_dairy": ["egg", "egg_white", "milk", "yogurt", "cheese", "steamed_egg", "tea_egg"],
    "vegetable": ["broccoli", "spinach", "tomato", "cucumber", "carrot", "lettuce", "cabbage", "celery", "bell_pepper", "mushroom", "potato", "tofu", "eggplant", "bok_choy", "cauliflower", "green_bean", "onion", "garlic", "ginger", "pumpkin", "lotus_root", "bamboo_shoot", "stir_fried_greens"],
    "fruit": ["apple", "banana", "orange", "grape", "watermelon", "strawberry", "blueberry", "avocado", "kiwi", "pineapple", "pear", "peach", "mango", "cherry", "dragon_fruit", "durian", "lychee", "coconut", "pomelo"],
    "nut": ["almond", "walnut", "peanut", "cashew", "pistachio", "sunflower_seed"],
    "drink": ["coffee", "green_tea", "orange_juice", "cola", "soy_milk", "milk_tea", "beer", "red_wine", "rice_wine", "coconut_milk", "lemon_water"],
    "dish": ["kung_pao_chicken", "mapo_tofu", "sweet_sour_pork", "hotpot", "salad", "sushi", "pizza", "hamburger", "sandwich", "scrambled_egg_tomato", "fries", "cake", "cookie", "chocolate", "ice_cream", "potato_chips"],
}

WEIGHT_ESTIMATE = {
    "rice": 200, "brown_rice": 200, "noodles": 250, "fried_rice": 250, "pasta": 200,
    "bread": 50, "whole_wheat_bread": 50, "steamed_bun": 100,
    "chicken_breast": 150, "chicken": 150, "chicken_leg": 120, "beef": 150, "steak": 200,
    "pork": 150, "lean_pork": 150, "lamb": 150, "duck": 150,
    "fish": 150, "salmon": 150, "shrimp": 100, "crab": 200, "squid": 100,
    "egg": 50, "egg_white": 30, "milk": 250, "yogurt": 200, "soy_milk": 250,
    "broccoli": 200, "spinach": 200, "tomato": 150, "cucumber": 150,
    "carrot": 150, "lettuce": 100, "cabbage": 200, "celery": 150,
    "bell_pepper": 150, "mushroom": 150, "potato": 200, "tofu": 200,
    "apple": 200, "banana": 120, "orange": 200, "grape": 200,
    "watermelon": 300, "strawberry": 150, "blueberry": 100,
    "avocado": 150, "kiwi": 100, "pineapple": 200,
    "almond": 30, "walnut": 30, "peanut": 30, "cashew": 30,
    "coffee": 300, "green_tea": 300, "orange_juice": 300, "cola": 330,
    "kung_pao_chicken": 250, "mapo_tofu": 250, "sweet_sour_pork": 250,
    "hotpot": 500, "salad": 250, "sushi": 200, "pizza": 200,
    "hamburger": 200, "sandwich": 200, "dumpling": 200, "corn": 200,
    "sweet_potato": 200, "oatmeal": 50, "cheese": 30,
    "porridge": 300, "congee": 300, "millet_porridge": 300, "wonton": 250,
    "baozi": 150, "spring_roll": 100, "rice_noodle": 250, "udon": 250,
    "ramen": 400, "fried_noodles": 300, "beef_noodles": 400,
    "braised_pork": 150, "twice_cooked_pork": 200, "spicy_chicken": 200,
    "sweet_sour_chicken": 200, "beef_broccoli": 200, "fish_fragrant_pork": 200,
    "fried_chicken": 200, "sausage": 100, "bacon": 50, "ham": 50,
    "steamed_egg": 150, "tea_egg": 60,
    "eggplant": 200, "bok_choy": 200, "cauliflower": 200, "green_bean": 150,
    "onion": 100, "garlic": 10, "ginger": 10, "pumpkin": 200,
    "lotus_root": 150, "bamboo_shoot": 150, "stir_fried_greens": 200,
    "pear": 200, "peach": 150, "mango": 200, "cherry": 100,
    "dragon_fruit": 250, "durian": 200, "lychee": 200, "coconut": 100,
    "pomelo": 250,
    "pistachio": 30, "sunflower_seed": 30,
    "milk_tea": 500, "beer": 500, "red_wine": 150, "rice_wine": 150,
    "coconut_milk": 250, "lemon_water": 300,
    "fries": 150, "cake": 100, "cookie": 30, "chocolate": 30,
    "ice_cream": 100, "potato_chips": 50, "instant_noodles": 100,
    "toast": 50, "croissant": 60, "scrambled_egg_tomato": 200,
}


# ============ 工具函数 ============

def calculate_nutrition(food_key, weight_g):
    if food_key not in FOOD_NUTRITION_DB:
        return None
    data = FOOD_NUTRITION_DB[food_key]
    ratio = weight_g / 100.0
    return {
        "food_key": food_key,
        "food_name_cn": data["name_cn"],
        "weight_g": round(weight_g, 1),
        "calorie": round(data["calorie"] * ratio, 1),
        "protein": round(data["protein"] * ratio, 1),
        "carb": round(data["carb"] * ratio, 1),
        "fat": round(data["fat"] * ratio, 1),
        "fiber": round(data["fiber"] * ratio, 1),
    }


# ============ 热量预算与运动消耗 ============

ACTIVITY_FACTOR = {
    "sedentary": 1.2,       # 久坐，几乎不运动
    "light": 1.375,         # 轻度运动（每周1-3次）
    "moderate": 1.55,       # 中度运动（每周3-5次）
    "active": 1.725,        # 高强度运动（每周6-7次）
    "very_active": 1.9,     # 极高强度（体力劳动/专业训练）
}

EXERCISE_MET = {
    "跑步": 9.8, "慢跑": 7.0, "快走": 4.3, "散步": 3.0,
    "游泳": 8.0, "骑行": 7.5, "跳绳": 11.0, "爬山": 6.5,
    "瑜伽": 3.0, "普拉提": 3.5, "力量训练": 6.0, "深蹲": 5.0,
    "俯卧撑": 8.0, "开合跳": 8.0, "波比跳": 10.0, "篮球": 6.5,
    "足球": 7.0, "羽毛球": 5.5, "乒乓球": 4.0, "网球": 7.3,
    "健身操": 6.0, "跳舞": 5.0, "太极拳": 3.5, "HIIT": 12.0,
}


def calc_bmr(profile):
    """Mifflin-St Jeor 公式计算基础代谢 BMR（kcal/天）"""
    if profile.gender == "female":
        return 10 * profile.weight_kg + 6.25 * profile.height_cm - 5 * profile.age - 161
    return 10 * profile.weight_kg + 6.25 * profile.height_cm - 5 * profile.age + 5


def calc_daily_budget(profile):
    """每日应摄入热量 = BMR * 活动系数"""
    bmr = calc_bmr(profile)
    factor = ACTIVITY_FACTOR.get(profile.activity_level, 1.375)
    return round(bmr * factor, 1)


def calc_exercise_burn(exercise_type, duration_min, weight_kg):
    """根据 MET 值计算运动消耗：消耗(kcal) = MET * 体重(kg) * 时长(小时)"""
    met = EXERCISE_MET.get(exercise_type, 5.0)
    return round(met * weight_kg * (duration_min / 60.0), 1)


# ============ 通义千问视觉识别配置 ============
# 免费获取 API Key: https://dashscope.console.aliyun.com/
# 新用户有 100 万 tokens 免费额度
# 密钥从环境变量 DASHSCOPE_API_KEY 读取（不要硬编码，避免上传泄露）
DASHSCOPE_API_KEY = os.environ.get("DASHSCOPE_API_KEY", "")


def _extract_json(content):
    """稳健地从模型输出中提取 JSON 对象（支持嵌套、代码块包裹、前后多余文字）"""
    if not content:
        return None
    # 去掉 markdown 代码块包裹
    content = re.sub(r"```(?:json)?\s*", "", content).replace("```", "").strip()
    # 优先尝试整体解析
    try:
        return json.loads(content)
    except Exception:
        pass
    # 用括号配对方式截取第一个完整 JSON 对象
    start = content.find("{")
    if start == -1:
        return None
    depth = 0
    for i in range(start, len(content)):
        if content[i] == "{":
            depth += 1
        elif content[i] == "}":
            depth -= 1
            if depth == 0:
                try:
                    return json.loads(content[start:i + 1])
                except Exception:
                    return None
    return None


def _match_food_key(food_name_cn):
    """将模型输出的食物名模糊匹配到 FOOD_NUTRITION_DB 的 key，返回 (food_key, 匹配方式)"""
    if not food_name_cn:
        return None, None
    name = food_name_cn.strip()
    # 1. 精确匹配
    for key, info in FOOD_NUTRITION_DB.items():
        if info["name_cn"] == name:
            return key, "exact"
    # 2. 包含匹配（模型输出 "白米饭" 能命中 "米饭"）
    for key, info in FOOD_NUTRITION_DB.items():
        if info["name_cn"] and (info["name_cn"] in name or name in info["name_cn"]):
            return key, "partial"
    return None, None


def _clamp_weight(weight_g, food_key):
    """将模型估算的重量约束到合理范围，避免离谱数值"""
    default = WEIGHT_ESTIMATE.get(food_key, 200)
    try:
        weight_g = int(weight_g)
    except (TypeError, ValueError):
        return default
    # 合理范围：默认值的 0.3 ~ 3 倍，且不低于 10g、不高于 2000g
    lo = max(10, int(default * 0.3))
    hi = min(2000, int(default * 3))
    return max(lo, min(weight_g, hi))


def ai_recognize_food(image_path):
    """使用通义千问视觉模型识别食物"""
    if not DASHSCOPE_API_KEY:
        return None

    try:
        with open(image_path, "rb") as f:
            image_base64 = base64.b64encode(f.read()).decode("utf-8")

        # 获取文件扩展名确定 MIME 类型
        ext = os.path.splitext(image_path)[1].lower()
        mime_map = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png", ".gif": "image/gif", ".webp": "image/webp"}
        mime_type = mime_map.get(ext, "image/jpeg")

        food_list = "、".join([v["name_cn"] for v in FOOD_NUTRITION_DB.values()])

        prompt = f"""你是一个专业的食物营养分析助手。请分析这张图片中的食物。

要求：
1. 识别图片中是什么食物
2. 从以下食物列表中选择最匹配的一个：{food_list}
3. 只输出 JSON 格式，不要任何其他文字

输出格式示例：
{{"food_name_cn": "米饭", "confidence": 0.9}}

注意：
- food_name_cn 必须从上述食物列表中选择，不要自己编造
- confidence 是 0-1 之间的置信度
- 不要估算重量，重量由用户自行输入
"""

        resp = requests.post(
            "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {DASHSCOPE_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": "qwen3-vl-plus",
                "messages": [{
                    "role": "user",
                    "content": [
                        {"type": "image_url", "image_url": {"url": f"data:{mime_type};base64,{image_base64}"}},
                        {"type": "text", "text": prompt},
                    ]
                }],
                "max_tokens": 200,
            },
            timeout=30,
        )

        if resp.status_code != 200:
            print(f"API error: {resp.status_code} {resp.text}")
            return None

        result = resp.json()
        content = result["choices"][0]["message"]["content"].strip()

        data = _extract_json(content)
        if not data:
            print(f"No JSON found in response: {content}")
            return None

        food_name_cn = data.get("food_name_cn", "")
        food_key, match_type = _match_food_key(food_name_cn)

        if not food_key:
            print(f"Food not in DB: {food_name_cn}")
            return None

        # 重量不再由 AI 估算，改用该食物的默认参考份量作为初始值，由用户在前端调整
        weight_g = WEIGHT_ESTIMATE.get(food_key, 200)

        # 模糊匹配时适当下调置信度
        confidence = float(data.get("confidence", 0.85))
        if match_type == "partial":
            confidence = min(confidence, 0.8)
        confidence = max(0.0, min(confidence, 1.0))

        return {
            "food_key": food_key,
            "confidence": confidence,
            "estimated_weight_g": weight_g,
        }

    except Exception as e:
        print(f"AI recognition error: {e}")
        return None


def update_daily_summary(user_id, record_date):
    records = FoodRecord.query.filter(
        FoodRecord.user_id == user_id,
        db.func.date(FoodRecord.created_at) == record_date
    ).all()
    total_cal = sum(r.calorie for r in records)
    total_protein = sum(r.protein for r in records)
    total_carb = sum(r.carb for r in records)
    total_fat = sum(r.fat for r in records)
    summary = DailySummary.query.filter_by(user_id=user_id, record_date=record_date).first()
    if summary:
        summary.total_calorie = round(total_cal, 1)
        summary.total_protein = round(total_protein, 1)
        summary.total_carb = round(total_carb, 1)
        summary.total_fat = round(total_fat, 1)
        summary.meal_count = len(records)
        summary.updated_at = datetime.utcnow()
    else:
        summary = DailySummary(
            user_id=user_id, record_date=record_date,
            total_calorie=round(total_cal, 1), total_protein=round(total_protein, 1),
            total_carb=round(total_carb, 1), total_fat=round(total_fat, 1),
            meal_count=len(records),
        )
        db.session.add(summary)
    db.session.commit()
    return summary


# ============ 静态资源 ============

@app.route("/static/uploads/<path:filename>")
def serve_upload(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)


# ============ 帖子 API ============

@app.route("/api/posts", methods=["GET"])
def get_posts():
    user_id = request.args.get("user_id", 1, type=int)
    only_mine = request.args.get("mine", "0") == "1"
    query = Post.query
    if only_mine:
        query = query.filter_by(user_id=user_id)
    posts = query.order_by(Post.id.desc()).all()
    # 当前用户点赞过的帖子 id 集合
    liked_ids = {l.post_id for l in Like.query.filter_by(user_id=user_id).all()}
    result = []
    for p in posts:
        comment_count = Comment.query.filter_by(post_id=p.id).count()
        result.append({
            "id": p.id, "user_id": p.user_id, "username": p.username,
            "content": p.content,
            "image_urls": p.image_urls.split(",") if p.image_urls else [],
            "like_count": p.like_count,
            "liked": p.id in liked_ids,
            "comment_count": comment_count,
            "time": p.time.strftime("%Y-%m-%d %H:%M:%S"),
        })
    return jsonify(result)


@app.route("/api/posts", methods=["POST"])
def add_post():
    content = request.form.get("content", "").strip()
    files = request.files.getlist("images")
    user_id = request.form.get("user_id", 1, type=int)
    username = request.form.get("username", "匿名用户")
    if not content:
        return jsonify({"msg": "内容不能为空"}), 400
    image_urls = []
    for file in files:
        if file and file.filename:
            ext = os.path.splitext(file.filename)[1]
            new_filename = str(uuid.uuid4()) + ext
            file.save(os.path.join(app.config["UPLOAD_FOLDER"], new_filename))
            image_urls.append(f"http://localhost:5000/static/uploads/{new_filename}")
    db.session.add(Post(user_id=user_id, username=username, content=content, image_urls=",".join(image_urls)))
    db.session.commit()
    return jsonify({"msg": "发布成功"}), 200


@app.route("/api/posts/<int:post_id>", methods=["DELETE"])
def delete_post(post_id):
    post = Post.query.get(post_id)
    if not post:
        return jsonify({"error": "动态不存在"}), 404
    # 删除关联评论和点赞
    Comment.query.filter_by(post_id=post_id).delete()
    Like.query.filter_by(post_id=post_id).delete()
    db.session.delete(post)
    db.session.commit()
    return jsonify({"success": True, "msg": "已删除"})


# ============ 点赞 API ============

@app.route("/api/posts/<int:post_id>/like", methods=["POST"])
def like_post(post_id):
    data = request.get_json() or {}
    user_id = data.get("user_id", 1)
    post = Post.query.get(post_id)
    if not post:
        return jsonify({"error": "动态不存在"}), 404
    existing = Like.query.filter_by(post_id=post_id, user_id=user_id).first()
    if existing:
        db.session.delete(existing)
        post.like_count = max(0, post.like_count - 1)
        db.session.commit()
        return jsonify({"success": True, "liked": False, "like_count": post.like_count})
    db.session.add(Like(post_id=post_id, user_id=user_id))
    post.like_count += 1
    db.session.commit()
    return jsonify({"success": True, "liked": True, "like_count": post.like_count})


# ============ 评论 API ============

@app.route("/api/posts/<int:post_id>/comments", methods=["GET"])
def get_comments(post_id):
    comments = Comment.query.filter_by(post_id=post_id).order_by(Comment.created_at.asc()).all()
    return jsonify([{
        "id": c.id, "user_id": c.user_id, "username": c.username,
        "content": c.content,
        "created_at": c.created_at.strftime("%Y-%m-%d %H:%M:%S"),
    } for c in comments])


@app.route("/api/posts/<int:post_id>/comments", methods=["POST"])
def add_comment(post_id):
    data = request.get_json() or {}
    content = data.get("content", "").strip()
    user_id = data.get("user_id", 1)
    username = data.get("username", "匿名用户")
    if not content:
        return jsonify({"error": "评论内容不能为空"}), 400
    comment = Comment(post_id=post_id, user_id=user_id, username=username, content=content)
    db.session.add(comment)
    db.session.commit()
    return jsonify({"success": True, "data": {
        "id": comment.id, "username": comment.username, "content": comment.content,
        "created_at": comment.created_at.strftime("%Y-%m-%d %H:%M:%S"),
    }}), 201


@app.route("/api/comments/<int:comment_id>", methods=["DELETE"])
def delete_comment(comment_id):
    comment = Comment.query.get(comment_id)
    if not comment:
        return jsonify({"error": "评论不存在"}), 404
    db.session.delete(comment)
    db.session.commit()
    return jsonify({"success": True, "msg": "已删除"})


# ============ AI 食物识别 API ============

@app.route("/api/food/recognize", methods=["POST"])
def recognize_food():
    if "image" not in request.files:
        return jsonify({"error": "请上传食物图片"}), 400
    file = request.files["image"]
    if not file or not file.filename:
        return jsonify({"error": "无效的文件"}), 400
    ext = os.path.splitext(file.filename)[1]
    if ext.lower() not in [".jpg", ".jpeg", ".png", ".gif", ".webp"]:
        return jsonify({"error": "仅支持 JPG/PNG/GIF/WEBP 格式"}), 400
    new_filename = str(uuid.uuid4()) + ext
    save_path = os.path.join(app.config["UPLOAD_FOLDER"], new_filename)
    file.save(save_path)
    image_url = f"http://localhost:5000/static/uploads/{new_filename}"
    # 优先使用 AI 识别，失败则返回明确错误（不再用随机模拟误导用户）
    recognition = ai_recognize_food(save_path)  # save_path defined above
    if not recognition:
        print("AI recognition failed")
        return jsonify({"error": "未能识别图片中的食物，请换一张更清晰、食物主体更明显的图片重试"}), 422

    nutrition = calculate_nutrition(recognition["food_key"], recognition["estimated_weight_g"])
    if not nutrition:
        return jsonify({"error": "未能识别食物，请重试"}), 400
    nutrition["image_url"] = image_url
    nutrition["confidence"] = recognition["confidence"]
    return jsonify({"success": True, "data": nutrition})


@app.route("/api/food/recognize_batch", methods=["POST"])
def recognize_food_batch():
    files = request.files.getlist("images")
    if not files:
        return jsonify({"error": "请上传食物图片"}), 400
    results = []
    for file in files:
        if not file or not file.filename:
            continue
        ext = os.path.splitext(file.filename)[1]
        if ext.lower() not in [".jpg", ".jpeg", ".png", ".gif", ".webp"]:
            continue
        new_filename = str(uuid.uuid4()) + ext
        save_path = os.path.join(app.config["UPLOAD_FOLDER"], new_filename)
        file.save(save_path)
        image_url = f"http://localhost:5000/static/uploads/{new_filename}"
        recognition = ai_recognize_food(save_path)
        if not recognition:
            continue
        nutrition = calculate_nutrition(recognition["food_key"], recognition["estimated_weight_g"])
        if nutrition:
            nutrition["image_url"] = image_url
            nutrition["confidence"] = recognition["confidence"]
            results.append(nutrition)
    return jsonify({"success": True, "data": results})


# ============ 食物数据查询 API ============

@app.route("/api/food/search", methods=["GET"])
def search_food():
    keyword = request.args.get("keyword", "").strip().lower()
    if not keyword:
        return jsonify({"error": "请输入搜索关键词"}), 400
    results = []
    for key, data in FOOD_NUTRITION_DB.items():
        if keyword in key or keyword in data["name_cn"]:
            results.append({
                "food_key": key, "food_name_cn": data["name_cn"],
                "calorie": data["calorie"], "protein": data["protein"],
                "carb": data["carb"], "fat": data["fat"], "fiber": data["fiber"],
            })
    return jsonify({"success": True, "data": results, "total": len(results)})


@app.route("/api/food/nutrition/<food_key>", methods=["GET"])
def get_food_nutrition(food_key):
    weight_g = request.args.get("weight", 200, type=float)
    nutrition = calculate_nutrition(food_key, weight_g)
    if not nutrition:
        return jsonify({"error": "未找到该食物数据"}), 404
    return jsonify({"success": True, "data": nutrition})


@app.route("/api/food/nutrition_list", methods=["GET"])
def get_nutrition_list():
    category = request.args.get("category", "all")
    results = []
    for key, data in FOOD_NUTRITION_DB.items():
        if category == "all" or key in CATEGORY_MAP.get(category, []):
            results.append({
                "food_key": key, "food_name_cn": data["name_cn"],
                "calorie": data["calorie"], "protein": data["protein"],
                "carb": data["carb"], "fat": data["fat"], "fiber": data["fiber"],
            })
    return jsonify({
        "success": True, "data": results, "total": len(results),
        "categories": list(CATEGORY_MAP.keys())
    })


# ============ 食物记录 CRUD ============

@app.route("/api/food/records", methods=["GET"])
def get_food_records():
    filter_date = request.args.get("date")
    meal_type = request.args.get("meal_type")
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    query = FoodRecord.query
    if filter_date:
        query = query.filter(db.func.date(FoodRecord.created_at) == filter_date)
    if meal_type:
        query = query.filter_by(meal_type=meal_type)
    query = query.order_by(FoodRecord.created_at.desc())
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    records = [{
        "id": r.id, "user_id": r.user_id, "meal_type": r.meal_type,
        "food_name": r.food_name, "food_name_cn": r.food_name_cn,
        "weight_g": r.weight_g, "calorie": r.calorie,
        "protein": r.protein, "carb": r.carb, "fat": r.fat, "fiber": r.fiber,
        "image_url": r.image_url, "confidence": r.confidence,
        "note": r.note, "created_at": r.created_at.strftime("%Y-%m-%d %H:%M:%S"),
    } for r in pagination.items]
    return jsonify({
        "success": True, "data": records, "total": pagination.total,
        "page": page, "per_page": per_page, "pages": pagination.pages,
    })


@app.route("/api/food/records", methods=["POST"])
def create_food_record():
    data = request.get_json()
    if not data:
        return jsonify({"error": "请求数据为空"}), 400
    food_name = data.get("food_name", data.get("food_key", ""))
    if not food_name:
        return jsonify({"error": "食物名称不能为空"}), 400
    record = FoodRecord(
        user_id=data.get("user_id", 1),
        meal_type=data.get("meal_type", "lunch"),
        food_name=food_name,
        food_name_cn=data.get("food_name_cn", ""),
        weight_g=data.get("weight_g", 200),
        calorie=data.get("calorie", 0),
        protein=data.get("protein", 0),
        carb=data.get("carb", 0),
        fat=data.get("fat", 0),
        fiber=data.get("fiber", 0),
        image_url=data.get("image_url", ""),
        confidence=data.get("confidence", 0),
        note=data.get("note", ""),
    )
    db.session.add(record)
    db.session.commit()
    today = date.today()
    update_daily_summary(data.get("user_id", 1), today)
    return jsonify({
        "success": True,
        "data": {
            "id": record.id,
            "food_name": record.food_name,
            "food_name_cn": record.food_name_cn,
            "calorie": record.calorie,
            "created_at": record.created_at.strftime("%Y-%m-%d %H:%M:%S"),
        }
    }), 201


@app.route("/api/food/records/<int:record_id>", methods=["PUT"])
def update_food_record(record_id):
    record = FoodRecord.query.get(record_id)
    if not record:
        return jsonify({"error": "记录不存在"}), 404
    data = request.get_json()
    if not data:
        return jsonify({"error": "请求数据为空"}), 400
    if "meal_type" in data:
        record.meal_type = data["meal_type"]
    if "weight_g" in data:
        record.weight_g = data["weight_g"]
        nutrition = calculate_nutrition(record.food_name, data["weight_g"])
        if nutrition:
            record.calorie = nutrition["calorie"]
            record.protein = nutrition["protein"]
            record.carb = nutrition["carb"]
            record.fat = nutrition["fat"]
            record.fiber = nutrition["fiber"]
    if "note" in data:
        record.note = data["note"]
    db.session.commit()
    update_daily_summary(record.user_id, date.today())
    return jsonify({"success": True, "msg": "更新成功"})


@app.route("/api/food/records/<int:record_id>", methods=["DELETE"])
def delete_food_record(record_id):
    record = FoodRecord.query.get(record_id)
    if not record:
        return jsonify({"error": "记录不存在"}), 404
    db.session.delete(record)
    db.session.commit()
    update_daily_summary(record.user_id, date.today())
    return jsonify({"success": True, "msg": "删除成功"})


# ============ 每日营养汇总 API ============

@app.route("/api/food/daily_summary", methods=["GET"])
def get_daily_summary():
    target_date = request.args.get("date", date.today().isoformat())
    user_id = request.args.get("user_id", 1, type=int)
    summary = DailySummary.query.filter_by(user_id=user_id, record_date=target_date).first()
    if not summary:
        return jsonify({
            "success": True,
            "data": {
                "record_date": target_date,
                "total_calorie": 0, "total_protein": 0,
                "total_carb": 0, "total_fat": 0, "meal_count": 0,
            }
        })
    return jsonify({
        "success": True,
        "data": {
            "record_date": summary.record_date.isoformat(),
            "total_calorie": summary.total_calorie,
            "total_protein": summary.total_protein,
            "total_carb": summary.total_carb,
            "total_fat": summary.total_fat,
            "meal_count": summary.meal_count,
        }
    })


@app.route("/api/food/weekly_summary", methods=["GET"])
def get_weekly_summary():
    user_id = request.args.get("user_id", 1, type=int)
    end_date = date.today()
    start_date = end_date - timedelta(days=6)
    summaries = DailySummary.query.filter(
        DailySummary.user_id == user_id,
        DailySummary.record_date >= start_date,
        DailySummary.record_date <= end_date
    ).order_by(DailySummary.record_date.asc()).all()
    summary_map = {s.record_date.isoformat(): s for s in summaries}
    # 补齐近 7 天，缺失的日期填 0，保证图表日期轴连续
    result = []
    for i in range(7):
        d = start_date + timedelta(days=i)
        key = d.isoformat()
        s = summary_map.get(key)
        result.append({
            "record_date": key,
            "total_calorie": s.total_calorie if s else 0,
            "total_protein": s.total_protein if s else 0,
            "total_carb": s.total_carb if s else 0,
            "total_fat": s.total_fat if s else 0,
            "meal_count": s.meal_count if s else 0,
        })
    return jsonify({"success": True, "data": result, "days": len(result)})


# 兼容旧接口
@app.route("/api/food", methods=["POST"])
def food():
    return jsonify({"food": "鸡胸肉", "calorie": 165})


# ============ 个人资料 API ============

@app.route("/api/profile", methods=["GET"])
def get_profile():
    user_id = request.args.get("user_id", 1, type=int)
    profile = UserProfile.query.filter_by(user_id=user_id).first()
    if not profile:
        return jsonify({"success": True, "data": None})
    return jsonify({"success": True, "data": {
        "nickname": profile.nickname, "avatar": profile.avatar,
        "signature": profile.signature, "contact": profile.contact,
        "gender": profile.gender, "age": profile.age,
        "height_cm": profile.height_cm, "weight_kg": profile.weight_kg,
        "activity_level": profile.activity_level,
    }})


@app.route("/api/profile", methods=["POST"])
def save_profile():
    data = request.get_json() or {}
    user_id = data.get("user_id", 1)
    profile = UserProfile.query.filter_by(user_id=user_id).first()
    if not profile:
        profile = UserProfile(user_id=user_id)
        db.session.add(profile)
    profile.nickname = data.get("nickname", profile.nickname)
    profile.avatar = data.get("avatar", profile.avatar)
    profile.signature = data.get("signature", profile.signature)
    profile.contact = data.get("contact", profile.contact)
    profile.gender = data.get("gender", "male")
    profile.age = int(data.get("age", 25))
    profile.height_cm = float(data.get("height_cm", 170))
    profile.weight_kg = float(data.get("weight_kg", 65))
    profile.activity_level = data.get("activity_level", "light")
    db.session.commit()
    return jsonify({"success": True, "data": {
        "nickname": profile.nickname, "avatar": profile.avatar,
        "signature": profile.signature, "contact": profile.contact,
        "gender": profile.gender, "age": profile.age,
        "height_cm": profile.height_cm, "weight_kg": profile.weight_kg,
        "activity_level": profile.activity_level,
    }})


@app.route("/api/profile/avatar", methods=["POST"])
def upload_avatar():
    if "file" not in request.files:
        return jsonify({"error": "请上传图片"}), 400
    file = request.files["file"]
    if not file or not file.filename:
        return jsonify({"error": "文件无效"}), 400
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in (".jpg", ".jpeg", ".png", ".gif", ".webp"):
        return jsonify({"error": "仅支持图片格式"}), 400
    new_filename = "avatar_" + str(uuid.uuid4()) + ext
    file.save(os.path.join(app.config["UPLOAD_FOLDER"], new_filename))
    url = f"http://localhost:5000/static/uploads/{new_filename}"
    return jsonify({"success": True, "url": url})


# ============ 每日热量预算 API ============

@app.route("/api/budget", methods=["GET"])
def get_budget():
    user_id = request.args.get("user_id", 1, type=int)
    target_date = request.args.get("date", date.today().isoformat())
    profile = UserProfile.query.filter_by(user_id=user_id).first()
    if not profile:
        return jsonify({"success": True, "data": {
            "has_profile": False, "daily_budget": None,
            "food_calorie": 0, "exercise_burn": 0, "remaining": None,
        }})

    daily_budget = calc_daily_budget(profile)

    # 今日摄入（食物）
    summary = DailySummary.query.filter_by(user_id=user_id, record_date=target_date).first()
    food_calorie = summary.total_calorie if summary else 0

    # 今日运动消耗
    exercises = ExerciseRecord.query.filter(
        ExerciseRecord.user_id == user_id,
        ExerciseRecord.record_date == target_date
    ).all()
    exercise_burn = round(sum(e.calorie_burn for e in exercises), 1)

    # 还可摄入 = 每日预算 + 运动消耗 - 已摄入
    remaining = round(daily_budget + exercise_burn - food_calorie, 1)

    return jsonify({"success": True, "data": {
        "has_profile": True,
        "daily_budget": daily_budget,
        "food_calorie": round(food_calorie, 1),
        "exercise_burn": exercise_burn,
        "remaining": remaining,
    }})


# ============ 运动记录 API ============

@app.route("/api/exercise", methods=["GET"])
def get_exercises():
    user_id = request.args.get("user_id", 1, type=int)
    target_date = request.args.get("date", date.today().isoformat())
    records = ExerciseRecord.query.filter(
        ExerciseRecord.user_id == user_id,
        ExerciseRecord.record_date == target_date
    ).order_by(ExerciseRecord.created_at.desc()).all()
    return jsonify({"success": True, "data": [{
        "id": r.id, "exercise_type": r.exercise_type,
        "duration_min": r.duration_min, "calorie_burn": r.calorie_burn,
        "created_at": r.created_at.strftime("%Y-%m-%d %H:%M:%S"),
    } for r in records]})


@app.route("/api/exercise", methods=["POST"])
def add_exercise():
    data = request.get_json() or {}
    user_id = data.get("user_id", 1)
    exercise_type = data.get("exercise_type", "").strip()
    duration_min = float(data.get("duration_min", 30))
    if not exercise_type:
        return jsonify({"error": "请填写运动类型"}), 400
    profile = UserProfile.query.filter_by(user_id=user_id).first()
    weight_kg = profile.weight_kg if profile else 65
    calorie_burn = calc_exercise_burn(exercise_type, duration_min, weight_kg)
    record = ExerciseRecord(
        user_id=user_id, exercise_type=exercise_type,
        duration_min=duration_min, calorie_burn=calorie_burn,
    )
    db.session.add(record)
    db.session.commit()
    return jsonify({"success": True, "data": {
        "id": record.id, "exercise_type": record.exercise_type,
        "duration_min": record.duration_min, "calorie_burn": record.calorie_burn,
        "created_at": record.created_at.strftime("%Y-%m-%d %H:%M:%S"),
    }}), 201


@app.route("/api/exercise/<int:record_id>", methods=["DELETE"])
def delete_exercise(record_id):
    record = ExerciseRecord.query.get(record_id)
    if not record:
        return jsonify({"error": "记录不存在"}), 404
    db.session.delete(record)
    db.session.commit()
    return jsonify({"success": True, "msg": "已删除"})


@app.route("/api/exercise/types", methods=["GET"])
def get_exercise_types():
    return jsonify({"success": True, "data": list(EXERCISE_MET.keys())})


@app.route("/api/pose", methods=["POST"])
def pose():
    return jsonify({"pose": "深蹲", "correct": True})


# ============ 健身商城 API ============

# 商品种子数据（首次启动时自动填充）
PRODUCT_SEED = [
    {"name": "可调节哑铃 20kg", "category": "器材", "price": 299, "original_price": 399, "description": "一对可调节重量哑铃，家用健身必备，铸钢材质，防滑手柄。", "stock": 50, "sales": 1200, "image": "https://picsum.photos/seed/dumbbell/400/400"},
    {"name": "瑜伽垫 加厚防滑", "category": "器材", "price": 59, "original_price": 99, "description": "10mm 加厚 TPE 瑜伽垫，防滑耐磨，附赠绑带。", "stock": 200, "sales": 3500, "image": "https://picsum.photos/seed/yogamat/400/400"},
    {"name": "健腹轮 自动回弹", "category": "器材", "price": 39, "original_price": 69, "description": "自动回弹健腹轮，静音设计，锻炼核心肌群。", "stock": 150, "sales": 2800, "image": "https://picsum.photos/seed/abwheel/400/400"},
    {"name": "弹力带套装 5件套", "category": "器材", "price": 45, "original_price": 79, "description": "不同阻力等级弹力带，适合全身训练，便携耐用。", "stock": 180, "sales": 4100, "image": "https://picsum.photos/seed/band/400/400"},
    {"name": "乳清蛋白粉 5磅", "category": "补剂", "price": 399, "original_price": 499, "description": "进口乳清蛋白，每份 24g 蛋白质，增肌必备。", "stock": 80, "sales": 2200, "image": "https://picsum.photos/seed/protein/400/400"},
    {"name": "肌酸粉 300g", "category": "补剂", "price": 129, "original_price": 169, "description": "一水肌酸，提升力量与爆发力，训练前服用。", "stock": 120, "sales": 1600, "image": "https://picsum.photos/seed/creatine/400/400"},
    {"name": "BCAA 支链氨基酸", "category": "补剂", "price": 159, "original_price": 219, "description": "支链氨基酸，减少肌肉分解，加速恢复。", "stock": 90, "sales": 980, "image": "https://picsum.photos/seed/bcaa/400/400"},
    {"name": "左旋肉碱 减脂胶囊", "category": "补剂", "price": 99, "original_price": 139, "description": "左旋肉碱，辅助脂肪代谢，配合有氧效果更佳。", "stock": 140, "sales": 1300, "image": "https://picsum.photos/seed/carnitine/400/400"},
    {"name": "速干运动T恤", "category": "服饰", "price": 89, "original_price": 129, "description": "透气速干面料，吸湿排汗，运动更舒适。", "stock": 300, "sales": 5200, "image": "https://picsum.photos/seed/tshirt/400/400"},
    {"name": "运动短裤 弹力透气", "category": "服饰", "price": 79, "original_price": 119, "description": "高弹力速干短裤，带内衬，跑步健身两用。", "stock": 260, "sales": 3800, "image": "https://picsum.photos/seed/shorts/400/400"},
    {"name": "训练手套 防滑", "category": "服饰", "price": 49, "original_price": 79, "description": "加厚护掌训练手套，防滑耐磨，保护手腕。", "stock": 180, "sales": 2100, "image": "https://picsum.photos/seed/gloves/400/400"},
    {"name": "护膝 运动保护", "category": "服饰", "price": 69, "original_price": 109, "description": "专业运动护膝，支撑保护，减少运动损伤。", "stock": 160, "sales": 1900, "image": "https://picsum.photos/seed/kneepad/400/400"},
]


def _ensure_products():
    if Product.query.count() == 0:
        for p in PRODUCT_SEED:
            db.session.add(Product(**p))
        db.session.commit()


@app.route("/api/products", methods=["GET"])
def get_products():
    _ensure_products()
    category = request.args.get("category", "all")
    keyword = request.args.get("keyword", "").strip()
    query = Product.query
    if category != "all":
        query = query.filter_by(category=category)
    if keyword:
        query = query.filter(Product.name.like(f"%{keyword}%"))
    products = query.order_by(Product.sales.desc()).all()
    return jsonify({"success": True, "data": [{
        "id": p.id, "name": p.name, "category": p.category,
        "price": p.price, "original_price": p.original_price,
        "image": p.image, "description": p.description,
        "stock": p.stock, "sales": p.sales,
    } for p in products]})


@app.route("/api/products/categories", methods=["GET"])
def get_product_categories():
    cats = db.session.query(Product.category).distinct().all()
    return jsonify({"success": True, "data": [c[0] for c in cats]})


@app.route("/api/products/<int:product_id>", methods=["GET"])
def get_product(product_id):
    product = Product.query.get(product_id)
    if not product:
        return jsonify({"error": "商品不存在"}), 404
    return jsonify({"success": True, "data": {
        "id": product.id, "name": product.name, "category": product.category,
        "price": product.price, "original_price": product.original_price,
        "image": product.image, "description": product.description,
        "stock": product.stock, "sales": product.sales,
    }})


@app.route("/api/orders", methods=["POST"])
def create_order():
    data = request.get_json() or {}
    user_id = data.get("user_id", 1)
    items = data.get("items", [])
    if not items:
        return jsonify({"error": "购物车为空"}), 400
    total = 0
    for it in items:
        total += float(it.get("price", 0)) * int(it.get("quantity", 1))
    order = Order(
        user_id=user_id,
        items=json.dumps(items, ensure_ascii=False),
        total_price=round(total, 2),
        status="待发货",
    )
    db.session.add(order)
    db.session.commit()
    return jsonify({"success": True, "data": {"order_id": order.id, "total_price": order.total_price}}), 201


@app.route("/api/orders", methods=["GET"])
def get_orders():
    user_id = request.args.get("user_id", 1, type=int)
    orders = Order.query.filter_by(user_id=user_id).order_by(Order.created_at.desc()).all()
    return jsonify({"success": True, "data": [{
        "id": o.id, "items": json.loads(o.items) if o.items else [],
        "total_price": o.total_price, "status": o.status,
        "created_at": o.created_at.strftime("%Y-%m-%d %H:%M:%S"),
    } for o in orders]})


# ===== 前端静态文件托管（生产部署：后端同端口提供前端 dist）=====
FRONTEND_DIST = os.path.join(os.path.dirname(app.root_path), 'frontend', 'dist')

@app.route('/')
def serve_index():
    return send_from_directory(FRONTEND_DIST, 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    # 优先尝试返回静态文件，不存在则回退到 index.html（支持前端路由）
    full = os.path.join(FRONTEND_DIST, path)
    if os.path.isfile(full):
        return send_from_directory(FRONTEND_DIST, path)
    return send_from_directory(FRONTEND_DIST, 'index.html')


if __name__ == "__main__":
    app.run(debug=True, port=5000)