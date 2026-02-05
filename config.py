import os
from dotenv import load_dotenv

# Load environment variables dari file .env
load_dotenv()

class Config:
    """Konfigurasi aplikasi dari environment variables"""
    
    # MongoDB Configuration
    MONGODB_URI = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/')
    
    # Database Names
    DB_MEMBER = os.getenv('DB_MEMBER', 'db_hdpayn_asli')
    DB_JUAL = os.getenv('DB_JUAL', 'db_hdpayn_asli')
    DB_BELI = os.getenv('DB_BELI', 'db_hdpayn_asli')
    
    # Collections
    COLLECTION_TT_MEMBER = os.getenv('COLLECTION_TT_MEMBER', 'tt_member')
    COLLECTION_TT_JUAL_DETAIL = os.getenv('COLLECTION_TT_JUAL_DETAIL', 'tt_jual_detail')
    COLLECTION_TT_BELI_DETAIL = os.getenv('COLLECTION_TT_BELI_DETAIL', 'tt_beli_detail')
    COLLECTION_TT_HUTANG_DETAIL = os.getenv('COLLECTION_TT_HUTANG_DETAIL', 'tt_hutang_detail')
    
    # File Paths (untuk mode JSON)
    JSON_TT_MEMBER = os.getenv('JSON_TT_MEMBER', 'tt_member.json')
    JSON_TT_JUAL_DETAIL = os.getenv('JSON_TT_JUAL_DETAIL', 'tt_jual_detail.json')
    JSON_OUTPUT = os.getenv('JSON_OUTPUT', 'tt_member_barcode_patched.json')
    
    @classmethod
    def get_mongodb_client(cls):
        """Mendapatkan MongoDB client"""
        from pymongo import MongoClient
        return MongoClient(cls.MONGODB_URI)
    
    @classmethod
    def get_database(cls, db_name=None):
        """Mendapatkan database instance"""
        client = cls.get_mongodb_client()
        if db_name:
            return client[db_name]
        return client[cls.DB_MEMBER]
    
    @classmethod
    def get_all_databases(cls):
        """Mendapatkan semua database instances"""
        client = cls.get_mongodb_client()
        return {
            'member': client[cls.DB_MEMBER],
            'jual': client[cls.DB_JUAL],
            'beli': client[cls.DB_BELI]
        }
    
    @classmethod
    def get_db_jual_for_branch(cls, branch_code):
        """
        Mendapatkan nama database jual untuk kode cabang/toko tertentu
        
        Args:
            branch_code: Kode cabang/toko (misal: AN1, AN2, AN3)
        
        Returns:
            str: Nama database atau None jika tidak ditemukan
        """
        env_key = f'DB_JUAL_{branch_code}'
        return os.getenv(env_key, cls.DB_JUAL)  # Return default DB_JUAL if not found
    
    @classmethod
    def get_all_db_jual_branches(cls):
        """
        Mendapatkan semua database jual untuk setiap cabang
        
        Returns:
            dict: {branch_code: database_name}
        """
        branches = {}
        for key, value in os.environ.items():
            if key.startswith('DB_JUAL_') and key != 'DB_JUAL':
                branch_code = key.replace('DB_JUAL_', '')
                branches[branch_code] = value
        return branches
    
    @classmethod
    def print_config(cls):
        """Menampilkan konfigurasi saat ini"""
        print("="*60)
        print("CONFIGURATION")
        print("="*60)
        print(f"MongoDB URI: {cls.MONGODB_URI[:30]}... (hidden)")
        print(f"DB Member: {cls.DB_MEMBER}")
        print(f"DB Jual: {cls.DB_JUAL}")
        print(f"DB Beli: {cls.DB_BELI}")
        print(f"Collection tt_member: {cls.COLLECTION_TT_MEMBER}")
        print(f"Collection tt_jual_detail: {cls.COLLECTION_TT_JUAL_DETAIL}")
        print(f"Collection tt_beli_detail: {cls.COLLECTION_TT_BELI_DETAIL}")
        print(f"Collection tt_hutang_detail: {cls.COLLECTION_TT_HUTANG_DETAIL}")
        print("="*60)

if __name__ == "__main__":
    # Test konfigurasi
    Config.print_config()
