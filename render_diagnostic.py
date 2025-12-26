#!/usr/bin/env python3
"""
Render Disk Diagnostic - Run this on your Render deployment
Access via: https://YOUR_APP.onrender.com/?diagnostic=true
"""

import os
import sys
import sqlite3
from pathlib import Path
import time

def render_disk_diagnostic():
    """Generate HTML diagnostic report for Render disk storage"""
    
    html_parts = []
    html_parts.append("<html><head><title>Render Disk Diagnostic</title>")
    html_parts.append("<style>")
    html_parts.append("body { font-family: monospace; background: #1a1a2e; color: #eee; padding: 20px; }")
    html_parts.append(".pass { color: #4caf50; }")
    html_parts.append(".fail { color: #f44336; }")
    html_parts.append(".warn { color: #ff9800; }")
    html_parts.append("table { border-collapse: collapse; margin: 10px 0; }")
    html_parts.append("td, th { border: 1px solid #555; padding: 8px; text-align: left; }")
    html_parts.append("</style></head><body>")
    
    html_parts.append("<h1>🔍 Render Disk Storage Diagnostic</h1>")
    html_parts.append(f"<p>Generated: {time.strftime('%Y-%m-%d %H:%M:%S UTC')}</p>")
    html_parts.append("<hr>")
    
    # Check 1: Mount path
    html_parts.append("<h2>1. Mount Path Status</h2>")
    if os.path.exists('/data'):
        html_parts.append(f"<p class='pass'>✅ /data mount EXISTS</p>")
        mount_path = Path('/data')
    else:
        html_parts.append(f"<p class='fail'>❌ /data mount NOT FOUND (using local fallback)</p>")
        mount_path = Path('./data')
        mount_path.mkdir(parents=True, exist_ok=True)
    
    html_parts.append(f"<p>Active path: <code>{mount_path}</code></p>")
    
    # Check 2: Permissions
    html_parts.append("<h2>2. File System Permissions</h2>")
    html_parts.append("<table>")
    html_parts.append("<tr><th>Test</th><th>Status</th><th>Details</th></tr>")
    
    # Write test
    test_file = mount_path / f'test_{int(time.time())}.txt'
    try:
        with open(test_file, 'w') as f:
            f.write("test")
        html_parts.append("<tr><td>Write</td><td class='pass'>✅ PASS</td><td>Can create files</td></tr>")
        write_ok = True
    except Exception as e:
        html_parts.append(f"<tr><td>Write</td><td class='fail'>❌ FAIL</td><td>{e}</td></tr>")
        write_ok = False
    
    # Read test
    if write_ok:
        try:
            with open(test_file, 'r') as f:
                f.read()
            html_parts.append("<tr><td>Read</td><td class='pass'>✅ PASS</td><td>Can read files</td></tr>")
        except Exception as e:
            html_parts.append(f"<tr><td>Read</td><td class='fail'>❌ FAIL</td><td>{e}</td></tr>")
        
        # Delete test
        try:
            test_file.unlink()
            html_parts.append("<tr><td>Delete</td><td class='pass'>✅ PASS</td><td>Can delete files</td></tr>")
        except Exception as e:
            html_parts.append(f"<tr><td>Delete</td><td class='fail'>❌ FAIL</td><td>{e}</td></tr>")
    
    html_parts.append("</table>")
    
    # Check 3: Disk usage
    html_parts.append("<h2>3. Disk Usage</h2>")
    try:
        import shutil
        total, used, free = shutil.disk_usage(mount_path)
        html_parts.append("<table>")
        html_parts.append(f"<tr><td>Total</td><td>{total / (1024**3):.2f} GB</td></tr>")
        html_parts.append(f"<tr><td>Used</td><td>{used / (1024**3):.2f} GB</td></tr>")
        html_parts.append(f"<tr><td>Free</td><td>{free / (1024**3):.2f} GB</td></tr>")
        html_parts.append(f"<tr><td>Usage</td><td>{(used/total)*100:.1f}%</td></tr>")
        html_parts.append("</table>")
    except Exception as e:
        html_parts.append(f"<p class='warn'>⚠️ Could not get disk usage: {e}</p>")
    
    # Check 4: tracker.db status
    html_parts.append("<h2>4. tracker.db Status</h2>")
    db_path = mount_path / 'tracker.db'
    
    if db_path.exists():
        html_parts.append(f"<p class='pass'>✅ tracker.db EXISTS</p>")
        html_parts.append(f"<p>Location: <code>{db_path}</code></p>")
        html_parts.append(f"<p>Size: {db_path.stat().st_size:,} bytes ({db_path.stat().st_size / 1024:.1f} KB)</p>")
        
        # Check WAL files
        wal_path = Path(str(db_path) + '-wal')
        shm_path = Path(str(db_path) + '-shm')
        
        if wal_path.exists():
            html_parts.append(f"<p class='pass'>✅ WAL file: {wal_path.stat().st_size:,} bytes</p>")
        else:
            html_parts.append(f"<p class='warn'>⚠️ No WAL file found</p>")
        
        if shm_path.exists():
            html_parts.append(f"<p class='pass'>✅ SHM file: {shm_path.stat().st_size:,} bytes</p>")
        else:
            html_parts.append(f"<p class='warn'>⚠️ No SHM file found</p>")
        
        # Try to connect and query
        try:
            conn = sqlite3.connect(db_path)
            
            # Check journal mode
            cursor = conn.execute("PRAGMA journal_mode")
            mode = cursor.fetchone()[0]
            if mode.upper() == 'WAL':
                html_parts.append(f"<p class='pass'>✅ Journal mode: {mode}</p>")
            else:
                html_parts.append(f"<p class='warn'>⚠️ Journal mode: {mode} (expected WAL)</p>")
            
            # Check tables
            cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            html_parts.append(f"<p>Tables: {', '.join(tables)}</p>")
            
            # Check record counts
            html_parts.append("<table>")
            html_parts.append("<tr><th>Table</th><th>Record Count</th></tr>")
            
            if 'markets' in tables:
                cursor = conn.execute("SELECT COUNT(*) FROM markets")
                count = cursor.fetchone()[0]
                html_parts.append(f"<tr><td>markets</td><td>{count:,}</td></tr>")
            
            if 'cumulative' in tables:
                cursor = conn.execute("SELECT COUNT(*) FROM cumulative")
                count = cursor.fetchone()[0]
                html_parts.append(f"<tr><td>cumulative</td><td>{count:,}</td></tr>")
            
            if 'prev_snapshot' in tables:
                cursor = conn.execute("SELECT COUNT(*) FROM prev_snapshot")
                count = cursor.fetchone()[0]
                html_parts.append(f"<tr><td>prev_snapshot</td><td>{count:,}</td></tr>")
            
            html_parts.append("</table>")
            
            # Check integrity
            cursor = conn.execute("PRAGMA integrity_check")
            result = cursor.fetchone()[0]
            if result == 'ok':
                html_parts.append(f"<p class='pass'>✅ Database integrity: OK</p>")
            else:
                html_parts.append(f"<p class='fail'>❌ Database integrity: {result}</p>")
            
            conn.close()
            
        except Exception as e:
            html_parts.append(f"<p class='fail'>❌ Database error: {e}</p>")
    else:
        html_parts.append(f"<p class='warn'>⚠️ tracker.db does NOT exist yet</p>")
        html_parts.append(f"<p>Expected location: <code>{db_path}</code></p>")
        html_parts.append(f"<p>This is normal if the tracker hasn't run yet.</p>")
    
    # Check 5: Environment variables
    html_parts.append("<h2>5. Environment Variables</h2>")
    html_parts.append("<table>")
    env_vars = ['PORT', 'RENDER', 'RENDER_SERVICE_NAME', 'RENDER_INSTANCE_ID', 'USE_DEMO_LOGIN']
    for var in env_vars:
        value = os.environ.get(var, 'Not set')
        html_parts.append(f"<tr><td>{var}</td><td>{value}</td></tr>")
    html_parts.append("</table>")
    
    # Check 6: File listing
    html_parts.append("<h2>6. Files in Mount Path</h2>")
    try:
        files = list(mount_path.iterdir())
        if files:
            html_parts.append("<ul>")
            for file in sorted(files):
                size = file.stat().st_size if file.is_file() else '-'
                file_type = 'DIR' if file.is_dir() else 'FILE'
                html_parts.append(f"<li>[{file_type}] {file.name} ({size:,} bytes)</li>")
            html_parts.append("</ul>")
        else:
            html_parts.append("<p>No files found in mount path</p>")
    except Exception as e:
        html_parts.append(f"<p class='fail'>❌ Could not list files: {e}</p>")
    
    html_parts.append("<hr>")
    html_parts.append("<p><small>To run this diagnostic again, visit: /?diagnostic=true</small></p>")
    html_parts.append("</body></html>")
    
    return ''.join(html_parts)


if __name__ == '__main__':
    # Run as standalone script
    print(render_disk_diagnostic().replace('<br>', '\n').replace('<p>', '\n').replace('</p>', ''))
