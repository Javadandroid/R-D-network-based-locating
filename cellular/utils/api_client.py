from ..models import CellTower

def fetch_and_save_tower(mcc, mnc, cell_id, lac, pci=None):
    """
    جستجوی دکل توری در دیتابیس یا ایجاد موقت
    
    اگر دکل پیدا شد: (tower_obj, 'LOCAL_DB')
    اگر نپیدا شد: (mock_tower, 'TEMPORARY')
    """
    
    # 1. جستجو در دیتابیس محلی
    if lac:
        try:
            tower = CellTower.objects.get(mcc=mcc, mnc=mnc, cell_id=cell_id, lac=lac)
            return tower, "LOCAL_DB"
        except CellTower.DoesNotExist:
            pass
    
    # 2. جستجو بدون LAC (Fallback)
    try:
        tower = CellTower.objects.filter(mcc=mcc, mnc=mnc, cell_id=cell_id).first()
        if tower:
            return tower, "LOCAL_DB"
    except:
        pass
    
    # 3. اگر پیدا نشد، یک موقت برگردان (برای توسعه و تست)
    # این موارد از مختصات تهران استفاده می‌کند
    class MockTower:
        def __init__(self, mcc, mnc, cell_id):
            self.mcc = mcc
            self.mnc = mnc
            self.cell_id = cell_id
            self.lat = 35.6892  # تهران
            self.lon = 51.3890  # تهران
            self.tx_power = 40  # پیش‌فرض
            self.pci = 0
            self.lac = 0
    
    return MockTower(mcc, mnc, cell_id), "TEMPORARY"