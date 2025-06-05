#!/usr/bin/env python3

import os
import sys
import json
import shutil
import sqlite3
import tarfile
import argparse
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from src.config import settings
from src.database import get_database


class SmartLampBackup:
    """Smart Lamp data backup utility."""
    
    def __init__(self, backup_dir: str = "./backups"):
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(exist_ok=True)
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.backup_name = f"smart_lamp_backup_{self.timestamp}"
        self.backup_path = self.backup_dir / self.backup_name
        self.backup_path.mkdir(exist_ok=True)
        
    def backup_database(self) -> bool:
        """Backup SQLite database."""
        print("📦 Backing up database...")
        
        try:
            db_path = settings.system.database_path
            if os.path.exists(db_path):
                backup_db_path = self.backup_path / "smart_lamp.db"
                shutil.copy2(db_path, backup_db_path)
                
                # Also export as JSON for readability
                db = get_database()
                
                # Export recent data
                export_data = {
                    'backup_timestamp': datetime.now().isoformat(),
                    'user_interactions': db.get_user_interactions(hours_back=24*30),  # Last 30 days
                    'environmental_data': db.get_environmental_data(hours_back=24*30),
                    'system_events': db.get_system_events(hours_back=24*30),
                    'usage_patterns': db.get_usage_patterns(days_back=30)
                }
                
                json_path = self.backup_path / "database_export.json"
                with open(json_path, 'w') as f:
                    json.dump(export_data, f, indent=2, default=str)
                
                print("✅ Database backup completed")
                return True
            else:
                print("⚠️  Database file not found")
                return False
                
        except Exception as e:
            print(f"❌ Database backup failed: {e}")
            return False
    
    def backup_ml_models(self) -> bool:
        """Backup ML models."""
        print("🧠 Backing up ML models...")
        
        try:
            models_dir = Path(settings.system.model_save_path)
            if models_dir.exists():
                backup_models_dir = self.backup_path / "models"
                shutil.copytree(models_dir, backup_models_dir, dirs_exist_ok=True)
                print("✅ ML models backup completed")
                return True
            else:
                print("⚠️  Models directory not found")
                return False
                
        except Exception as e:
            print(f"❌ ML models backup failed: {e}")
            return False
    
    def backup_configuration(self) -> bool:
        """Backup configuration files."""
        print("⚙️ Backing up configuration...")
        
        try:
            config_files = ['.env', 'env.example', 'requirements.txt']
            config_backup_dir = self.backup_path / "config"
            config_backup_dir.mkdir(exist_ok=True)
            
            for config_file in config_files:
                if os.path.exists(config_file):
                    shutil.copy2(config_file, config_backup_dir / config_file)
            
            # Save current settings as JSON
            settings_export = {
                'backup_timestamp': datetime.now().isoformat(),
                'api_settings': {
                    'earthquake_api_url': settings.api.earthquake_api_url,
                    'earthquake_check_interval': settings.api.earthquake_check_interval,
                    'earthquake_min_magnitude': settings.api.earthquake_min_magnitude,
                    'openweather_base_url': settings.api.openweather_base_url,
                    'air_quality_threshold': settings.api.air_quality_threshold,
                    'temp_check_interval': settings.api.temp_check_interval,
                    'latitude': settings.api.latitude,
                    'longitude': settings.api.longitude,
                    'location_name': settings.api.location_name,
                },
                'hardware_settings': {
                    'main_button_pin': settings.hardware.main_button_pin,
                    'color_button_pin': settings.hardware.color_button_pin,
                    'mode_button_pin': settings.hardware.mode_button_pin,
                    'led_strip_pin': settings.hardware.led_strip_pin,
                    'led_strip_count': settings.hardware.led_strip_count,
                    'audio_device': settings.hardware.audio_device,
                    'speaker_volume': settings.hardware.speaker_volume,
                },
                'system_settings': {
                    'web_host': settings.system.web_host,
                    'web_port': settings.system.web_port,
                    'debug_mode': settings.system.debug_mode,
                    'default_brightness': settings.system.default_brightness,
                    'default_color_r': settings.system.default_color_r,
                    'default_color_g': settings.system.default_color_g,
                    'default_color_b': settings.system.default_color_b,
                    'radio_stations': settings.system.radio_stations,
                }
            }
            
            settings_path = config_backup_dir / "settings_export.json"
            with open(settings_path, 'w') as f:
                json.dump(settings_export, f, indent=2)
            
            print("✅ Configuration backup completed")
            return True
            
        except Exception as e:
            print(f"❌ Configuration backup failed: {e}")
            return False
    
    def backup_logs(self) -> bool:
        """Backup log files."""
        print("📋 Backing up logs...")
        
        try:
            logs_sources = [
                Path("data/logs"),
                Path("data/usage_logs.json"),
                Path("data/lamp_state.json")
            ]
            
            logs_backup_dir = self.backup_path / "logs"
            logs_backup_dir.mkdir(exist_ok=True)
            
            for source in logs_sources:
                if source.exists():
                    if source.is_dir():
                        dest = logs_backup_dir / source.name
                        shutil.copytree(source, dest, dirs_exist_ok=True)
                    else:
                        shutil.copy2(source, logs_backup_dir / source.name)
            
            print("✅ Logs backup completed")
            return True
            
        except Exception as e:
            print(f"❌ Logs backup failed: {e}")
            return False
    
    def backup_audio_files(self) -> bool:
        """Backup custom audio files."""
        print("🎵 Backing up audio files...")
        
        try:
            audio_dir = Path(settings.system.ambient_sounds_path)
            if audio_dir.exists():
                backup_audio_dir = self.backup_path / "audio"
                shutil.copytree(audio_dir, backup_audio_dir, dirs_exist_ok=True)
                print("✅ Audio files backup completed")
                return True
            else:
                print("⚠️  Audio directory not found")
                return False
                
        except Exception as e:
            print(f"❌ Audio files backup failed: {e}")
            return False
    
    def create_backup_manifest(self, results: Dict[str, bool]) -> None:
        """Create backup manifest with metadata."""
        print("📄 Creating backup manifest...")
        
        manifest = {
            'backup_name': self.backup_name,
            'timestamp': datetime.now().isoformat(),
            'version': '1.0.0',
            'components': results,
            'total_size_bytes': self._calculate_backup_size(),
            'backup_path': str(self.backup_path),
            'system_info': {
                'python_version': sys.version,
                'platform': sys.platform,
                'cwd': os.getcwd()
            }
        }
        
        manifest_path = self.backup_path / "manifest.json"
        with open(manifest_path, 'w') as f:
            json.dump(manifest, f, indent=2)
        
        print("✅ Backup manifest created")
    
    def _calculate_backup_size(self) -> int:
        """Calculate total size of backup."""
        total_size = 0
        for dirpath, dirnames, filenames in os.walk(self.backup_path):
            for filename in filenames:
                filepath = os.path.join(dirpath, filename)
                total_size += os.path.getsize(filepath)
        return total_size
    
    def create_archive(self, compress: bool = True) -> Optional[str]:
        """Create compressed archive of backup."""
        print("📦 Creating backup archive...")
        
        try:
            if compress:
                archive_name = f"{self.backup_name}.tar.gz"
                archive_path = self.backup_dir / archive_name
                
                with tarfile.open(archive_path, "w:gz") as tar:
                    tar.add(self.backup_path, arcname=self.backup_name)
            else:
                archive_name = f"{self.backup_name}.tar"
                archive_path = self.backup_dir / archive_name
                
                with tarfile.open(archive_path, "w") as tar:
                    tar.add(self.backup_path, arcname=self.backup_name)
            
            # Remove uncompressed backup directory
            shutil.rmtree(self.backup_path)
            
            archive_size = os.path.getsize(archive_path)
            print(f"✅ Archive created: {archive_path} ({archive_size / (1024*1024):.1f} MB)")
            
            return str(archive_path)
            
        except Exception as e:
            print(f"❌ Archive creation failed: {e}")
            return None
    
    def run_backup(self, include_models: bool = True, include_audio: bool = True, 
                   create_archive: bool = True, compress: bool = True) -> Dict[str, Any]:
        """Run complete backup process."""
        print("🏮 Smart Lamp System Backup")
        print("=" * 40)
        print(f"📁 Backup location: {self.backup_path}")
        print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        results = {
            'database': self.backup_database(),
            'configuration': self.backup_configuration(),
            'logs': self.backup_logs()
        }
        
        if include_models:
            results['ml_models'] = self.backup_ml_models()
        
        if include_audio:
            results['audio_files'] = self.backup_audio_files()
        
        # Create manifest
        self.create_backup_manifest(results)
        
        # Create archive if requested
        archive_path = None
        if create_archive:
            archive_path = self.create_archive(compress)
        
        # Summary
        successful = sum(1 for success in results.values() if success)
        total = len(results)
        
        print("\n" + "=" * 40)
        print("📊 BACKUP SUMMARY")
        print("=" * 40)
        print(f"✅ Successful: {successful}/{total}")
        print(f"❌ Failed: {total - successful}/{total}")
        
        for component, success in results.items():
            status = "✅" if success else "❌"
            print(f"{status} {component.replace('_', ' ').title()}")
        
        if archive_path:
            print(f"\n📦 Archive: {archive_path}")
        
        backup_info = {
            'backup_name': self.backup_name,
            'timestamp': datetime.now().isoformat(),
            'results': results,
            'archive_path': archive_path,
            'success_rate': successful / total
        }
        
        return backup_info


def restore_backup(archive_path: str, restore_dir: str = "./") -> bool:
    """Restore from backup archive."""
    print(f"🔄 Restoring from backup: {archive_path}")
    
    try:
        with tarfile.open(archive_path, "r:*") as tar:
            tar.extractall(restore_dir)
        
        print("✅ Backup restored successfully")
        print("⚠️  Please review restored files before overwriting current system")
        return True
        
    except Exception as e:
        print(f"❌ Restore failed: {e}")
        return False


def list_backups(backup_dir: str = "./backups") -> List[Dict[str, Any]]:
    """List available backups."""
    backup_path = Path(backup_dir)
    if not backup_path.exists():
        return []
    
    backups = []
    for item in backup_path.iterdir():
        if item.is_file() and (item.suffix == '.gz' or item.suffix == '.tar'):
            stat = item.stat()
            backups.append({
                'name': item.name,
                'path': str(item),
                'size_mb': stat.st_size / (1024 * 1024),
                'created': datetime.fromtimestamp(stat.st_ctime).isoformat()
            })
    
    return sorted(backups, key=lambda x: x['created'], reverse=True)


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description='Smart Lamp System Backup Utility')
    parser.add_argument('--backup-dir', default='./backups', 
                       help='Backup directory (default: ./backups)')
    parser.add_argument('--no-models', action='store_true', 
                       help='Skip ML models backup')
    parser.add_argument('--no-audio', action='store_true', 
                       help='Skip audio files backup')
    parser.add_argument('--no-archive', action='store_true', 
                       help='Skip archive creation')
    parser.add_argument('--no-compress', action='store_true', 
                       help='Create uncompressed archive')
    parser.add_argument('--list', action='store_true', 
                       help='List available backups')
    parser.add_argument('--restore', type=str, 
                       help='Restore from backup archive')
    parser.add_argument('--restore-dir', default='./', 
                       help='Directory to restore to (default: ./)')
    
    args = parser.parse_args()
    
    if args.list:
        # List backups
        backups = list_backups(args.backup_dir)
        if backups:
            print("📦 Available Backups:")
            print("-" * 60)
            for backup in backups:
                print(f"📁 {backup['name']}")
                print(f"   Size: {backup['size_mb']:.1f} MB")
                print(f"   Created: {backup['created']}")
                print()
        else:
            print("No backups found.")
        return
    
    if args.restore:
        # Restore backup
        success = restore_backup(args.restore, args.restore_dir)
        sys.exit(0 if success else 1)
    
    # Create backup
    backup = SmartLampBackup(args.backup_dir)
    result = backup.run_backup(
        include_models=not args.no_models,
        include_audio=not args.no_audio,
        create_archive=not args.no_archive,
        compress=not args.no_compress
    )
    
    # Exit with appropriate code
    success_rate = result['success_rate']
    if success_rate == 1.0:
        print("\n🎉 Backup completed successfully!")
        sys.exit(0)
    elif success_rate > 0.5:
        print("\n⚠️  Backup completed with warnings")
        sys.exit(0)
    else:
        print("\n❌ Backup failed")
        sys.exit(1)


if __name__ == '__main__':
    main()
