import json
from dataclasses import dataclass
from typing import List, Tuple, Optional
from datetime import datetime
from pathlib import Path


@dataclass
class SilenceRegion:
    time_ms: int
    dbfs: float


@dataclass
class SilenceDetectionLog:
    timestamp: datetime
    marked_time: float
    marked_point_dbfs: float
    window_size: int
    silence_threshold: float
    silent_regions: List[List[SilenceRegion]]
    longest_region_length: Optional[float]
    adjusted_time: float
    adjusted_point_dbfs: float
    status: str
    error: Optional[str]

    @classmethod
    def from_log_line(cls, log_line: str) -> 'SilenceDetectionLog':
        # Extract JSON part from log line
        json_start = log_line.find('{')
        json_str = log_line[json_start:]
        data = json.loads(json_str)

        # Convert silent regions to structured format
        silent_regions = []
        for region_group in data['silent_regions']:
            regions = [
                SilenceRegion(time_ms=int(region[0]), dbfs=float(region[1]))
                for region in region_group
            ]
            silent_regions.append(regions)

        return cls(
            timestamp=datetime.fromisoformat(data['timestamp']),
            marked_time=data['marked_time'],
            marked_point_dbfs=data['marked_point_dbfs'],
            window_size=data['window_size'],
            silence_threshold=data['silence_threshold'],
            silent_regions=silent_regions,
            longest_region_length=data['longest_region_length'],
            adjusted_time=data['adjusted_time'],
            adjusted_point_dbfs=data['adjusted_point_dbfs'],
            status=data['status'],
            error=data['error']
        )


def analyze_silence_log_file(log_file_path):
    """Parse a log file and return structured data."""
    log_file_path = Path(log_file_path)
    if not log_file_path.exists():
        raise FileNotFoundError(f"Log file not found: {log_file_path}")

    logs = []
    with open(log_file_path, 'r') as file:
        for line in file:
            if 'silence_detection' in line and line.strip():
                try:
                    log_entry = SilenceDetectionLog.from_log_line(line)
                    logs.append(log_entry)
                except json.JSONDecodeError:
                    print(f"Warning: Skipping malformed log line: {line[:100]}...")
                except Exception as e:
                    print(f"Warning: Error processing line: {str(e)}")

    return logs


def generate_summary(logs: List[SilenceDetectionLog], output_file: Optional[str] = None) -> str:
    """Generate a human-readable summary of the silence detection logs."""
    summary = []
    summary.append("Silence Detection Summary:")
    summary.append("-" * 40)

    for i, log in enumerate(logs, 1):
        summary.append(f"\nEntry {i}:")
        summary.append(f"Time: {log.timestamp.strftime('%H:%M:%S')}")
        summary.append(f"Marked Time: {log.marked_time:.2f}s")
        summary.append(f"Number of Silent Regions: {len(log.silent_regions)}")
        if log.longest_region_length:
            summary.append(f"Longest Silent Region: {log.longest_region_length * 1000:.0f}ms")
        summary.append(f"Status: {log.status}")

    summary_text = "\n".join(summary)

    if output_file:
        with open(output_file, 'w') as f:
            f.write(summary_text)

    return summary_text


def main():
    output = "silence_detection_out.log"
    try:
        # Parse logs
        logs = analyze_silence_log_file("silence_detection.log")

        # Generate and display summary
        summary = generate_summary(logs, output)
        print(summary)

        if output:
            print(f"\nSummary saved to: {output}")

    except Exception as e:
        print(f"Error: {str(e)}")
        return 1

    return 0


if __name__ == "__main__":
    import sys

    sys.exit(main())