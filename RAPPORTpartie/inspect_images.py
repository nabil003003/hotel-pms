import fitz
import os
from PIL import Image

# Let's inspect images by creating a text summary of image contents or inspecting
# Let's write a small helper to inspect what is shown on key UI images
images = [
    'homepage.png',
    'reservation.png',
    'checkin.png',
    'businescheckin.png',
    'folio_1.png',
    'ajouter_charge.png',
    'business_date.png',
    'etabli.png',
    'names.png',
    'clients.png',
    'pms_link_qr.png',
    'passkey.png',
    'jeton.png',
    'table_.png',
    'news.png',
    'rq.png'
]

print("Images to check:")
for img_name in images:
    path = os.path.join('PMSV2-main/RAPPORTpartie/figures', img_name)
    exists = os.path.exists(path)
    print(f"  {img_name:30s} -> exists={exists}")
