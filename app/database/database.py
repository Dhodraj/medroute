import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path
from loguru import logger

from ..schemas import LogEntry


class DatabaseManager:
    """Manages SQLite database for triage logs"""
    
    def __init__(self, db_path: str = "triage.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize database with required tables"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Create triage_logs table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS triage_logs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        input_text TEXT NOT NULL,
                        symptoms TEXT NOT NULL,
                        triage_level TEXT NOT NULL,
                        recommendation TEXT NOT NULL,
                        confidence_score REAL,
                        llm_model_version TEXT NOT NULL,
                        processing_time_ms INTEGER,
                        timestamp DATETIME NOT NULL,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Create indexes for better query performance
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_triage_logs_timestamp 
                    ON triage_logs(timestamp)
                """)
                
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_triage_logs_triage_level 
                    ON triage_logs(triage_level)
                """)
                
                conn.commit()
                logger.info("Database initialized successfully")
                
        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
            raise
    
    def save_log_entry(self, log_entry: LogEntry) -> int:
        """Save a log entry to the database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT INTO triage_logs 
                    (input_text, symptoms, triage_level, recommendation, 
                     confidence_score, llm_model_version, processing_time_ms, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    log_entry.input_text,
                    log_entry.symptoms,
                    log_entry.triage_level,
                    log_entry.recommendation,
                    log_entry.confidence_score,
                    log_entry.llm_model_version,
                    log_entry.processing_time_ms,
                    log_entry.timestamp
                ))
                
                log_id = cursor.lastrowid
                conn.commit()
                
                return log_id
                
        except Exception as e:
            logger.error(f"Failed to save log entry: {e}")
            raise
    
    def get_recent_logs(self, limit: int = 10) -> List[LogEntry]:
        """Get recent log entries"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT * FROM triage_logs 
                    ORDER BY timestamp DESC 
                    LIMIT ?
                """, (limit,))
                
                rows = cursor.fetchall()
                
                log_entries = []
                for row in rows:
                    log_entry = LogEntry(
                        id=row['id'],
                        input_text=row['input_text'],
                        symptoms=row['symptoms'],
                        triage_level=row['triage_level'],
                        recommendation=row['recommendation'],
                        confidence_score=row['confidence_score'],
                        llm_model_version=row['llm_model_version'],
                        processing_time_ms=row['processing_time_ms'],
                        timestamp=datetime.fromisoformat(row['timestamp'])
                    )
                    log_entries.append(log_entry)
                
                return log_entries
                
        except Exception as e:
            logger.error(f"Failed to get recent logs: {e}")
            return []
    
    def get_logs_by_triage_level(self, triage_level: str, limit: int = 50) -> List[LogEntry]:
        """Get logs filtered by triage level"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT * FROM triage_logs 
                    WHERE triage_level = ?
                    ORDER BY timestamp DESC 
                    LIMIT ?
                """, (triage_level, limit))
                
                rows = cursor.fetchall()
                
                log_entries = []
                for row in rows:
                    log_entry = LogEntry(
                        id=row['id'],
                        input_text=row['input_text'],
                        symptoms=row['symptoms'],
                        triage_level=row['triage_level'],
                        recommendation=row['recommendation'],
                        confidence_score=row['confidence_score'],
                        llm_model_version=row['llm_model_version'],
                        processing_time_ms=row['processing_time_ms'],
                        timestamp=datetime.fromisoformat(row['timestamp'])
                    )
                    log_entries.append(log_entry)
                
                return log_entries
                
        except Exception as e:
            logger.error(f"Failed to get logs by triage level: {e}")
            return []
    
    def get_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Total logs
                cursor.execute("SELECT COUNT(*) FROM triage_logs")
                total_logs = cursor.fetchone()[0]
                
                # Logs by triage level
                cursor.execute("""
                    SELECT triage_level, COUNT(*) as count 
                    FROM triage_logs 
                    GROUP BY triage_level
                """)
                triage_counts = dict(cursor.fetchall())
                
                # Average confidence score
                cursor.execute("""
                    SELECT AVG(confidence_score) 
                    FROM triage_logs 
                    WHERE confidence_score IS NOT NULL
                """)
                avg_confidence = cursor.fetchone()[0]
                
                # Average processing time
                cursor.execute("""
                    SELECT AVG(processing_time_ms) 
                    FROM triage_logs 
                    WHERE processing_time_ms IS NOT NULL
                """)
                avg_processing_time = cursor.fetchone()[0]
                
                # Recent activity (last 24 hours)
                cursor.execute("""
                    SELECT COUNT(*) 
                    FROM triage_logs 
                    WHERE timestamp > datetime('now', '-1 day')
                """)
                recent_activity = cursor.fetchone()[0]
                
                return {
                    "total_logs": total_logs,
                    "triage_level_distribution": triage_counts,
                    "average_confidence_score": round(avg_confidence, 3) if avg_confidence else None,
                    "average_processing_time_ms": round(avg_processing_time, 2) if avg_processing_time else None,
                    "activity_last_24h": recent_activity
                }
                
        except Exception as e:
            logger.error(f"Failed to get database stats: {e}")
            return {}
    
    def cleanup_old_logs(self, days_to_keep: int = 30):
        """Clean up old log entries"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    DELETE FROM triage_logs 
                    WHERE timestamp < datetime('now', '-{} days')
                """.format(days_to_keep))
                
                deleted_count = cursor.rowcount
                conn.commit()
                
                logger.info(f"Cleaned up {deleted_count} old log entries")
                return deleted_count
                
        except Exception as e:
            logger.error(f"Failed to cleanup old logs: {e}")
            return 0
