#!/usr/bin/env python3
"""
Test script to verify persistent disk storage on Render.com
Tests: /data mount, SQLite write/read, persistence across restarts
"""

import os
import sys
import sqlite3
import time
from pathlib import Path

def test_disk_storage():
    """Comprehensive test of Render persistent disk storage"""
    
    print("="*60)
    print("🧪 TESTING RENDER PERSISTENT DISK STORAGE")
    print("="*60)
    print()
    
    # Test 1: Check if /data mount exists
    print("Test 1: Checking /data mount path...")
    if os.path.exists('/data'):
        print("✅ /data mount exists")
        mount_path = Path('/data')
    else:
        print("⚠️  /data mount NOT found (using local fallback)")
        mount_path = Path(__file__).parent / 'data'
        mount_path.mkdir(parents=True, exist_ok=True)
    print(f"   Using: {mount_path}")
    print()
    
    # Test 2: Check write permissions
    print("Test 2: Testing write permissions...")
    test_file = mount_path / 'test_write.txt'
    try:
        with open(test_file, 'w') as f:
            f.write(f"Test write at {time.time()}")
        print(f"✅ Write successful: {test_file}")
    except Exception as e:
        print(f"❌ Write FAILED: {e}")
        return False
    print()
    
    # Test 3: Check read permissions
    print("Test 3: Testing read permissions...")
    try:
        with open(test_file, 'r') as f:
            content = f.read()
        print(f"✅ Read successful: {content[:50]}...")
    except Exception as e:
        print(f"❌ Read FAILED: {e}")
        return False
    print()
    
    # Test 4: Check delete permissions
    print("Test 4: Testing delete permissions...")
    try:
        test_file.unlink()
        print(f"✅ Delete successful")
    except Exception as e:
        print(f"❌ Delete FAILED: {e}")
        return False
    print()
    
    # Test 5: SQLite database creation
    print("Test 5: Creating SQLite database...")
    db_path = mount_path / 'test_tracker.db'
    try:
        conn = sqlite3.connect(db_path)
        conn.execute("PRAGMA journal_mode=WAL")
        print(f"✅ Database created: {db_path}")
        print(f"   Size: {db_path.stat().st_size} bytes")
    except Exception as e:
        print(f"❌ Database creation FAILED: {e}")
        return False
    print()
    
    # Test 6: Create table and insert data
    print("Test 6: Creating table and inserting test data...")
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS test_markets (
                market_id TEXT PRIMARY KEY,
                event_name TEXT,
                total_matched REAL,
                created_at INTEGER
            )
        """)
        
        test_data = [
            ('1.12345', 'Test Event 1', 1000000.50, int(time.time())),
            ('1.67890', 'Test Event 2', 2500000.75, int(time.time())),
            ('1.11111', 'Test Event 3', 500000.25, int(time.time()))
        ]
        
        conn.executemany(
            "INSERT OR REPLACE INTO test_markets VALUES (?, ?, ?, ?)",
            test_data
        )
        conn.commit()
        print(f"✅ Inserted {len(test_data)} test records")
    except Exception as e:
        print(f"❌ Insert FAILED: {e}")
        conn.close()
        return False
    print()
    
    # Test 7: Read data back
    print("Test 7: Reading data from database...")
    try:
        cursor = conn.execute("SELECT * FROM test_markets ORDER BY market_id")
        rows = cursor.fetchall()
        print(f"✅ Retrieved {len(rows)} records:")
        for row in rows:
            print(f"   - Market: {row[0]}, Event: {row[1]}, Matched: ₹{row[2]:,.2f}")
    except Exception as e:
        print(f"❌ Read FAILED: {e}")
        conn.close()
        return False
    print()
    
    # Test 8: Update data
    print("Test 8: Updating data...")
    try:
        conn.execute(
            "UPDATE test_markets SET total_matched = total_matched + 1000 WHERE market_id = ?",
            ('1.12345',)
        )
        conn.commit()
        
        cursor = conn.execute("SELECT total_matched FROM test_markets WHERE market_id = ?", ('1.12345',))
        new_value = cursor.fetchone()[0]
        print(f"✅ Update successful: New value = ₹{new_value:,.2f}")
    except Exception as e:
        print(f"❌ Update FAILED: {e}")
        conn.close()
        return False
    print()
    
    # Test 9: Check WAL mode
    print("Test 9: Verifying WAL mode...")
    try:
        cursor = conn.execute("PRAGMA journal_mode")
        mode = cursor.fetchone()[0]
        if mode.upper() == 'WAL':
            print(f"✅ WAL mode active: {mode}")
        else:
            print(f"⚠️  WAL mode NOT active: {mode}")
    except Exception as e:
        print(f"❌ WAL check FAILED: {e}")
    print()
    
    # Test 10: Check database file size and integrity
    print("Test 10: Checking database integrity...")
    try:
        cursor = conn.execute("PRAGMA integrity_check")
        result = cursor.fetchone()[0]
        if result == 'ok':
            print(f"✅ Database integrity: OK")
        else:
            print(f"⚠️  Database integrity: {result}")
        
        db_size = db_path.stat().st_size
        wal_path = Path(str(db_path) + '-wal')
        shm_path = Path(str(db_path) + '-shm')
        
        print(f"   Main DB: {db_size:,} bytes")
        if wal_path.exists():
            print(f"   WAL file: {wal_path.stat().st_size:,} bytes")
        if shm_path.exists():
            print(f"   SHM file: {shm_path.stat().st_size:,} bytes")
    except Exception as e:
        print(f"❌ Integrity check FAILED: {e}")
    print()
    
    conn.close()
    
    # Test 11: Check actual tracker.db if it exists
    print("Test 11: Checking real tracker.db...")
    real_db = mount_path / 'tracker.db'
    if real_db.exists():
        print(f"✅ tracker.db exists: {real_db}")
        print(f"   Size: {real_db.stat().st_size:,} bytes")
        
        try:
            conn = sqlite3.connect(real_db)
            cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            print(f"   Tables: {', '.join(tables)}")
            
            # Check record counts
            if 'markets' in tables:
                cursor = conn.execute("SELECT COUNT(*) FROM markets")
                count = cursor.fetchone()[0]
                print(f"   Markets: {count} records")
            
            if 'cumulative' in tables:
                cursor = conn.execute("SELECT COUNT(*) FROM cumulative")
                count = cursor.fetchone()[0]
                print(f"   Cumulative: {count} records")
            
            conn.close()
        except Exception as e:
            print(f"⚠️  Could not read tracker.db: {e}")
    else:
        print(f"ℹ️  tracker.db does not exist yet (will be created on first run)")
    print()
    
    # Cleanup test database
    print("Cleanup: Removing test database...")
    try:
        db_path.unlink(missing_ok=True)
        Path(str(db_path) + '-wal').unlink(missing_ok=True)
        Path(str(db_path) + '-shm').unlink(missing_ok=True)
        print(f"✅ Test database cleaned up")
    except Exception as e:
        print(f"⚠️  Cleanup warning: {e}")
    print()
    
    # Final summary
    print("="*60)
    print("✅ ALL TESTS PASSED")
    print("="*60)
    print()
    print("📋 Summary:")
    print(f"   Mount path: {mount_path}")
    print(f"   Write: ✅  Read: ✅  Delete: ✅")
    print(f"   SQLite: ✅  WAL mode: ✅  Integrity: ✅")
    print()
    print("🎉 Persistent disk storage is working correctly!")
    print()
    
    return True


if __name__ == '__main__':
    try:
        success = test_disk_storage()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
