#!/usr/bin/env python3
"""
Siril Log Analyzer
==================
Analyzes Siril preprocessing log files to generate summary reports including:
- Execution timing for each phase
- Image counts and filtering waterfall
- Quality metrics and patterns
- Failure detection and debugging info

Usage:
    # Automatic (via main script):
    Check "Generate Summary Report" in Naztronomy Smart Telescope Preprocessor UI
    
    # Manual analysis:
    python siril_log_analyzer.py <log_file> [--output report.txt]
    
    # Examples:
    python siril_log_analyzer.py ~/.siril/siril.log
    python siril_log_analyzer.py m42siril.log --output report.txt
    python siril_log_analyzer.py recent.log --waterfall-only

Version: 1.0.0
Date: 2025-12-17

Author: Vinu Yamunan (with Gemini AI Assistant)
Created for: Nazmus Nasir (Naztronomy) - Naztronomy Smart Telescope Preprocessor
License: GPL-3.0-or-later (matching parent project)

This script is part of the Naztronomy Smart Telescope Preprocessing suite:
    Website: https://www.Naztronomy.com
    YouTube: https://www.YouTube.com/Naztronomy
    Discord: https://discord.gg/yXKqrawpjr
    

CHANGELOG:
    1.0.0 (2025-12-17) - Initial release
        - Phase timing extraction (conversion, plate solving, registration, stacking)
        - Image count tracking through processing pipeline
        - ASCII waterfall chart visualization
        - Pattern detection (plate solve failures, FWHM variation, mosaics)
        - Quality metrics and recommendations
        - CLI support with output file option
        - Failure-aware analysis for debugging partial runs
"""

import re
import sys
import argparse
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, field


@dataclass
class PhaseInfo:
    """Information about a processing phase"""
    name: str
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration: Optional[timedelta] = None
    image_count_in: Optional[int] = None
    image_count_out: Optional[int] = None
    failed: bool = False
    error_message: Optional[str] = None


@dataclass
class LogAnalysis:
    """Complete log analysis results"""
    phases: List[PhaseInfo] = field(default_factory=list)
    initial_images: int = 0
    final_images: int = 0
    plate_solve_failures: int = 0
    plate_solve_successes: int = 0
    fwhm_values: List[float] = field(default_factory=list)
    rotation_angles: List[float] = field(default_factory=list)
    rejection_stats: Dict[str, float] = field(default_factory=dict)
    processors_used: int = 0
    patterns: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    timestamp_gaps: List[Tuple[str, float]] = field(default_factory=list)


class SirilLogParser:
    """Parser for Siril log files"""
    
    def __init__(self, log_file_path: str):
        self.log_file = log_file_path
        self.analysis = LogAnalysis()
        self.log_lines = []
        
    def parse(self) -> LogAnalysis:
        """Main parsing method"""
        try:
            with open(self.log_file, 'r', encoding='utf-8') as f:
                self.log_lines = f.readlines()
        except Exception as e:
            self.analysis.errors.append(f"Failed to read log file: {e}")
            return self.analysis
        
        self._extract_initial_info()
        self._extract_conversion_phase()
        self._extract_plate_solve_phase()
        self._extract_background_phase()
        self._extract_registration_phase()
        self._extract_stacking_phase()
        self._detect_patterns()
        
        return self.analysis
    
    def _parse_timestamp(self, line: str) -> Optional[datetime]:
        """Extract timestamp from log line"""
        match = re.match(r'^(\d{2}:\d{2}:\d{2}):', line)
        if match:
            time_str = match.group(1)
            try:
                # Use a dummy date since logs don't include date
                return datetime.strptime(f"2000-01-01 {time_str}", "%Y-%m-%d %H:%M:%S")
            except:
                pass
        return None
    
    def _extract_initial_info(self):
        """Extract initial configuration info"""
        for line in self.log_lines:
            # Processor count
            if "Parallel processing enabled" in line:
                match = re.search(r'using (\d+) logical processors', line)
                if match:
                    self.analysis.processors_used = int(match.group(1))
    
    def _extract_conversion_phase(self):
        """Extract conversion phase information"""
        phase = PhaseInfo(name="File Conversion")
        
        for i, line in enumerate(self.log_lines):
            if "Convert: processing" in line:
                phase.start_time = self._parse_timestamp(line)
                match = re.search(r'processing (\d+) files', line)
                if match:
                    count = int(match.group(1))
                    phase.image_count_in = count
                    phase.image_count_out = count
                    if self.analysis.initial_images == 0:
                        self.analysis.initial_images = count
            
            elif "Converted" in line and "files for processing" in line:
                phase.end_time = self._parse_timestamp(line)
                match = re.search(r'Converted (\d+)', line)
                if match:
                    phase.image_count_out = int(match.group(1))
        
        if phase.start_time and phase.end_time:
            phase.duration = phase.end_time - phase.start_time
            self.analysis.phases.append(phase)
    
    def _extract_plate_solve_phase(self):
        """Extract plate solving phase information"""
        phase = PhaseInfo(name="Plate Solving")
        solved_count = 0
        failed_count = 0
        
        for i, line in enumerate(self.log_lines):
            if "platesolved and updated" in line:
                if not phase.start_time:
                    phase.start_time = self._parse_timestamp(line)
                phase.end_time = self._parse_timestamp(line)
                solved_count += 1
            
            elif "did not solve" in line:
                if not phase.start_time:
                    phase.start_time = self._parse_timestamp(line)
                phase.end_time = self._parse_timestamp(line)
                failed_count += 1
            
            # Summary line
            elif "images successfully platesolved out of" in line:
                match = re.search(r'(\d+) images successfully platesolved out of (\d+)', line)
                if match:
                    solved_count = int(match.group(1))
                    total = int(match.group(2))
                    failed_count = total - solved_count
                phase.end_time = self._parse_timestamp(line)
            
            # Extract FWHM values
            fwhm_match = re.search(r'FWHM (\d+\.\d+)', line)
            if fwhm_match:
                self.analysis.fwhm_values.append(float(fwhm_match.group(1)))
            
            # Extract rotation angles
            rotation_match = re.search(r'Rotation:\s+([\+\-]?\d+\.\d+)', line)
            if rotation_match:
                self.analysis.rotation_angles.append(float(rotation_match.group(1)))
        
        self.analysis.plate_solve_successes = solved_count
        self.analysis.plate_solve_failures = failed_count
        phase.image_count_in = solved_count + failed_count if solved_count + failed_count > 0 else None
        phase.image_count_out = solved_count if solved_count > 0 else None
        
        if phase.start_time and phase.end_time:
            phase.duration = phase.end_time - phase.start_time
            self.analysis.phases.append(phase)
    
    def _extract_background_phase(self):
        """Extract background extraction phase"""
        phase = PhaseInfo(name="Background Extraction")
        
        for line in self.log_lines:
            if "seqsubsky" in line.lower() or "background extracted" in line.lower():
                if not phase.start_time:
                    phase.start_time = self._parse_timestamp(line)
                phase.end_time = self._parse_timestamp(line)
        
        if phase.start_time and phase.end_time:
            phase.duration = phase.end_time - phase.start_time
            self.analysis.phases.append(phase)
    
    def _extract_registration_phase(self):
        """Extract registration phase"""
        phase = PhaseInfo(name="Registration")
        
        for line in self.log_lines:
            if "seqapplyreg" in line.lower() or "registered sequence" in line.lower():
                if not phase.start_time:
                    phase.start_time = self._parse_timestamp(line)
                phase.end_time = self._parse_timestamp(line)
        
        if phase.start_time and phase.end_time:
            phase.duration = phase.end_time - phase.start_time
            self.analysis.phases.append(phase)
    
    def _extract_stacking_phase(self):
        """Extract stacking phase"""
        phase = PhaseInfo(name="Stacking")
        
        for i, line in enumerate(self.log_lines):
            if "Starting stacking" in line:
                phase.start_time = self._parse_timestamp(line)
            
            elif "Stacked sequence successfully" in line or "Rejection stacking complete" in line:
                phase.end_time = self._parse_timestamp(line)
                
                # Look for image count in nearby lines
                for j in range(max(0, i-5), min(len(self.log_lines), i+1)):
                    match = re.search(r'(\d+) images have been stacked', self.log_lines[j])
                    if match:
                        phase.image_count_out = int(match.group(1))
                        self.analysis.final_images = int(match.group(1))
                        break
            
            # Extract rejection statistics
            elif "Pixel rejection in channel" in line:
                match = re.search(r'channel #(\d+):\s+([\d\.]+)%\s*-\s*([\d\.]+)%', line)
                if match:
                    channel = int(match.group(1))
                    low = float(match.group(2))
                    high = float(match.group(3))
                    self.analysis.rejection_stats[f"channel_{channel}"] = (low, high)
        
        if phase.start_time and phase.end_time:
            phase.duration = phase.end_time - phase.start_time
            self.analysis.phases.append(phase)
    
    def _detect_patterns(self):
        """Detect interesting patterns in the log"""
        patterns = []
        
        # Plate solving failures
        if self.analysis.plate_solve_failures > 0:
            total = self.analysis.plate_solve_successes + self.analysis.plate_solve_failures
            rate = (self.analysis.plate_solve_failures / total * 100) if total > 0 else 0
            patterns.append(f"⚠ Plate Solving: {self.analysis.plate_solve_failures} images ({rate:.1f}%) failed to solve")
        
        # Overall retention rate
        if self.analysis.initial_images > 0 and self.analysis.final_images > 0:
            retention = (self.analysis.final_images / self.analysis.initial_images * 100)
            lost = self.analysis.initial_images - self.analysis.final_images
            patterns.append(f"ℹ Overall Retention: {retention:.1f}% ({lost} images filtered/rejected)")
        
        # FWHM quality
        if self.analysis.fwhm_values:
            fwhm_min = min(self.analysis.fwhm_values)
            fwhm_max = max(self.analysis.fwhm_values)
            fwhm_avg = sum(self.analysis.fwhm_values) / len(self.analysis.fwhm_values)
            patterns.append(f"ℹ FWHM Range: {fwhm_min:.1f} - {fwhm_max:.1f} pixels (avg: {fwhm_avg:.1f})")
        
        # Rotation angle drift (mosaic detection)
        if self.analysis.rotation_angles:
            rot_min = min(self.analysis.rotation_angles)
            rot_max = max(self.analysis.rotation_angles)
            if abs(rot_max - rot_min) > 10:
                patterns.append(f"ℹ Mosaic Pattern: Rotation drift from {rot_min:.1f}° to {rot_max:.1f}° detected")
        
        # Processor utilization
        if self.analysis.processors_used > 0:
            patterns.append(f"ℹ Parallelization: {self.analysis.processors_used} logical processors utilized")
        
        # Rejection statistics
        if self.analysis.rejection_stats:
            patterns.append(f"ℹ Pixel Rejection: {self._format_rejection_stats()}")
        
        self.analysis.patterns = patterns
    
    def _format_rejection_stats(self) -> str:
        """Format rejection statistics"""
        if not self.analysis.rejection_stats:
            return "N/A"
        
        ranges = []
        for channel, (low, high) in self.analysis.rejection_stats.items():
            ranges.append(f"{low:.3f}%-{high:.3f}%")
        return ", ".join(ranges)
    
    def generate_waterfall(self) -> str:
        """Generate ASCII waterfall chart"""
        lines = []
        lines.append("=" * 60)
        lines.append("IMAGE PROCESSING WATERFALL")
        lines.append("=" * 60)
        
        # Calculate bar width
        max_count = self.analysis.initial_images
        bar_width = 40
        
        def make_bar(count: int, width: int = bar_width) -> str:
            if max_count == 0:
                return ""
            filled = int((count / max_count) * width)
            return "█" * filled
        
        def format_line(label: str, count: Optional[int], percentage: Optional[float] = None) -> str:
            if count is None:
                return f"{label:30s} N/A"
            bar = make_bar(count)
            pct_str = f" ({percentage:.0f}%)" if percentage is not None else ""
            return f"{label:30s} {count:4d} {bar}{pct_str}"
        
        # Initial
        lines.append(format_line("Initial Images", self.analysis.initial_images, 100))
        lines.append("  ↓")
        
        # Conversion
        conv_phase = next((p for p in self.analysis.phases if "Conversion" in p.name), None)
        if conv_phase and conv_phase.image_count_out:
            pct = (conv_phase.image_count_out / self.analysis.initial_images * 100) if self.analysis.initial_images > 0 else 0
            lines.append(format_line("After Conversion", conv_phase.image_count_out, pct))
            lines.append("  ↓")
        
        # Plate solving
        if self.analysis.plate_solve_successes > 0:
            pct = (self.analysis.plate_solve_successes / self.analysis.initial_images * 100) if self.analysis.initial_images > 0 else 0
            lines.append(format_line("After Plate Solving", self.analysis.plate_solve_successes, pct))
            if self.analysis.plate_solve_failures > 0:
                lines.append(f"  ├─ Failed to solve: {self.analysis.plate_solve_failures}")
            lines.append("  ↓")
        
        # Registration (same as plate solve success for now)
        reg_phase = next((p for p in self.analysis.phases if "Registration" in p.name), None)
        if reg_phase:
            count = reg_phase.image_count_out or self.analysis.plate_solve_successes
            pct = (count / self.analysis.initial_images * 100) if self.analysis.initial_images > 0 else 0
            lines.append(format_line("After Registration", count, pct))
            lines.append("  ↓")
        
        # Final stacking
        if self.analysis.final_images > 0:
            pct = (self.analysis.final_images / self.analysis.initial_images * 100) if self.analysis.initial_images > 0 else 0
            lines.append(format_line("Final Stacked Images", self.analysis.final_images, pct))
            
            # Calculate rejected
            pre_stack = self.analysis.plate_solve_successes or self.analysis.initial_images
            rejected = pre_stack - self.analysis.final_images
            if rejected > 0:
                lines.append(f"  ├─ Rejected/Filtered: {rejected}")
        
        lines.append("=" * 60)
        
        return "\n".join(lines)
    
    def generate_summary(self) -> str:
        """Generate complete summary report"""
        lines = []
        lines.append("")
        lines.append("=" * 60)
        lines.append("PROCESSING SUMMARY REPORT")
        lines.append("=" * 60)
        lines.append("")
        
        # [1] Execution Times
        lines.append("[1] EXECUTION TIMES")
        lines.append("-" * 30)
        
        total_duration = timedelta(0)
        for phase in self.analysis.phases:
            if phase.duration:
                total_duration += phase.duration
        
        if total_duration.total_seconds() > 0:
            lines.append(f"Total Duration:          {self._format_duration(total_duration)}")
            
            for phase in self.analysis.phases:
                if phase.duration:
                    pct = (phase.duration.total_seconds() / total_duration.total_seconds() * 100)
                    lines.append(f"  • {phase.name:20s} {self._format_duration(phase.duration):>10s} ({pct:5.1f}%)")
        else:
            lines.append("Total Duration:          Unable to determine")
            lines.append("(Timing information not available in log)")
        
        lines.append("")
        
        # [2] Waterfall
        lines.append("[2] IMAGE PROCESSING WATERFALL")
        lines.append("-" * 30)
        lines.append(self.generate_waterfall())
        lines.append("")
        
        # [3] Quality Metrics
        lines.append("[3] QUALITY METRICS")
        lines.append("-" * 30)
        lines.append(f"  • Initial Images:        {self.analysis.initial_images}")
        lines.append(f"  • Final Stacked Images:  {self.analysis.final_images}")
        
        if self.analysis.initial_images > 0 and self.analysis.final_images > 0:
            retention = (self.analysis.final_images / self.analysis.initial_images * 100)
            lines.append(f"  • Overall Retention:     {retention:.1f}%")
        
        if self.analysis.plate_solve_successes > 0:
            total = self.analysis.plate_solve_successes + self.analysis.plate_solve_failures
            success_rate = (self.analysis.plate_solve_successes / total * 100)
            lines.append(f"  • Plate Solve Success:   {success_rate:.1f}%")
        
        if self.analysis.fwhm_values:
            fwhm_min = min(self.analysis.fwhm_values)
            fwhm_max = max(self.analysis.fwhm_values)
            lines.append(f"  • FWHM Range:            {fwhm_min:.1f} - {fwhm_max:.1f} pixels")
        
        if self.analysis.rejection_stats:
            lines.append(f"  • Pixel Rejection:       {self._format_rejection_stats()}")
        
        lines.append("")
        
        # [4] Patterns
        if self.analysis.patterns:
            lines.append("[4] PATTERNS DETECTED")
            lines.append("-" * 30)
            for pattern in self.analysis.patterns:
                lines.append(f"  {pattern}")
            lines.append("")
        
        # [5] Recommendations
        lines.append("[5] RECOMMENDATIONS")
        lines.append("-" * 30)
        recommendations = self._generate_recommendations()
        for rec in recommendations:
            lines.append(f"  • {rec}")
        
        lines.append("")
        lines.append("=" * 60)
        
        return "\n".join(lines)
    
    def _generate_recommendations(self) -> List[str]:
        """Generate recommendations based on analysis"""
        recs = []
        
        # Plate solve success
        if self.analysis.plate_solve_successes > 0:
            total = self.analysis.plate_solve_successes + self.analysis.plate_solve_failures
            success_rate = (self.analysis.plate_solve_successes / total * 100)
            
            if success_rate >= 95:
                recs.append(f"Plate solve success rate is excellent ({success_rate:.1f}%)")
            elif success_rate >= 85:
                recs.append(f"Plate solve success rate is good ({success_rate:.1f}%)")
            else:
                recs.append(f"⚠ Low plate solve success rate ({success_rate:.1f}%) - check image quality")
        
        # Retention rate
        if self.analysis.initial_images > 0 and self.analysis.final_images > 0:
            retention = (self.analysis.final_images / self.analysis.initial_images * 100)
            loss = 100 - retention
            
            if retention >= 80:
                recs.append(f"{loss:.0f}% image loss is within normal range for quality filtering")
            elif retention >= 60:
                recs.append(f"⚠ {loss:.0f}% image loss - consider reviewing filter settings")
            else:
                recs.append(f"⚠ High image loss ({loss:.0f}%) - review quality filters and check for issues")
        
        # FWHM variation
        if self.analysis.fwhm_values and len(self.analysis.fwhm_values) > 10:
            fwhm_range = max(self.analysis.fwhm_values) - min(self.analysis.fwhm_values)
            if fwhm_range > 2.0:
                recs.append("ℹ High FWHM variation detected - seeing conditions may have changed during session")
        
        if not recs:
            recs.append("No specific recommendations - processing appears normal")
        
        return recs
    
    def _format_duration(self, td: timedelta) -> str:
        """Format timedelta as HH:MM:SS"""
        total_seconds = int(td.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    
    def save_report(self, output_path: str):
        """Save summary report to file"""
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(self.generate_summary())
            print(f"Report saved to: {output_path}")
        except Exception as e:
            print(f"Failed to save report: {e}")


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Analyze Siril preprocessing log files",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument('log_file', help='Path to Siril log file')
    parser.add_argument('-o', '--output', help='Save report to file (optional)')
    parser.add_argument('-w', '--waterfall-only', action='store_true', 
                       help='Show only waterfall chart')
    
    args = parser.parse_args()
    
    # Parse log
    analyzer = SirilLogParser(args.log_file)
    analysis = analyzer.parse()
    
    # Display errors if any
    if analysis.errors:
        print("Errors encountered:")
        for error in analysis.errors:
            print(f"  • {error}")
        print()
    
    # Generate and display report
    if args.waterfall_only:
        output = analyzer.generate_waterfall()
    else:
        output = analyzer.generate_summary()
    
    print(output)
    
    # Save if requested
    if args.output:
        analyzer.save_report(args.output)


if __name__ == "__main__":
    main()
