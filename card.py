# coding=utf-8
from db import db

def init(card):
    full_card = db.cards.find_one({'name': card})
    res = {
        'name': full_card['name'],
        'level': 1,
        'dmg': full_card['dmg'],
        'dmg_buff': 0,
        'hp': full_card['hp'],
        'active': False,
    }
    return res

def attack_card(card1, card2, boss):
    print 'attack card'
    card2['hp'] = card2['hp'] - card1['dmg']
    if card2['hp'] < 0:
        boss['hp'] = boss['hp'] + card2['hp']
    return card1, card2, boss

def attack_boss(card, boss):
    print 'attack boss'
    boss['hp'] = boss['hp'] - card['dmg']
    return card, boss