#!/bin/bash
# Find Generic Exception Handlers Script
# Helps identify files that need exception handling improvements

echo "=================================================="
echo "  Alpha AI Autotrader - Exception Handler Finder"
echo "=================================================="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Find all files with generic exception handlers
echo -e "${BLUE}Scanning backend directory...${NC}"
echo ""

total_files=0
total_occurrences=0

# Create temporary file for results
temp_file=$(mktemp)

# Find files and count occurrences
for file in $(grep -r "except Exception" backend/ --include="*.py" -l 2>/dev/null); do
    count=$(grep "except Exception" "$file" | wc -l)
    echo "$count|$file" >> "$temp_file"
done

# Sort by count (highest first) and display
if [ -s "$temp_file" ]; then
    echo -e "${YELLOW}Files with generic exception handlers (sorted by count):${NC}"
    echo "---------------------------------------------------"
    echo ""

    while IFS='|' read -r count file; do
        ((total_files++))
        ((total_occurrences += count))

        # Color code based on count
        if [ "$count" -ge 10 ]; then
            color=$RED
        elif [ "$count" -ge 5 ]; then
            color=$YELLOW
        else
            color=$GREEN
        fi

        printf "${color}%-4s${NC} %s\n" "[$count]" "$file"

        # Show first 3 occurrences
        grep -n "except Exception" "$file" 2>/dev/null | head -3 | while read -r line; do
            echo "       → Line: $line"
        done
        echo ""
    done < <(sort -t'|' -k1 -rn "$temp_file")

    echo "---------------------------------------------------"
    echo -e "${GREEN}Summary:${NC}"
    echo "  Total files: $total_files"
    echo "  Total occurrences: $total_occurrences"
    echo ""

    # Priority classification
    echo -e "${BLUE}Priority Classification:${NC}"
    echo ""

    echo -e "${RED}HIGH Priority${NC} (API & Integrations):"
    grep -E "(api/|integrations/)" "$temp_file" | sort -t'|' -k1 -rn | while IFS='|' read -r count file; do
        printf "  [%-3s] %s\n" "$count" "$file"
    done
    echo ""

    echo -e "${YELLOW}MEDIUM Priority${NC} (Core Logic):"
    grep -E "core/" "$temp_file" | sort -t'|' -k1 -rn | while IFS='|' read -r count file; do
        printf "  [%-3s] %s\n" "$count" "$file"
    done
    echo ""

    echo -e "${GREEN}LOW Priority${NC} (ML & Agents):"
    grep -E "(ml/|agents/)" "$temp_file" | sort -t'|' -k1 -rn | while IFS='|' read -r count file; do
        printf "  [%-3s] %s\n" "$count" "$file"
    done
    echo ""

    # Completion percentage
    completed_files=1  # routes.py partial
    percentage=$((completed_files * 100 / total_files))
    echo -e "${BLUE}Progress:${NC} $completed_files/$total_files files completed (${percentage}%)"
    echo ""

    # Save detailed report
    report_file="exception_handlers_report.txt"
    {
        echo "Exception Handlers Report"
        echo "Generated: $(date)"
        echo ""
        echo "Total files: $total_files"
        echo "Total occurrences: $total_occurrences"
        echo ""
        echo "Files (sorted by count):"
        echo "========================"
        sort -t'|' -k1 -rn "$temp_file" | while IFS='|' read -r count file; do
            printf "[%3s] %s\n" "$count" "$file"
            grep -n "except Exception" "$file" 2>/dev/null | sed 's/^/         Line /'
            echo ""
        done
    } > "$report_file"

    echo -e "${GREEN}Detailed report saved to: $report_file${NC}"
else
    echo -e "${GREEN}No generic exception handlers found! 🎉${NC}"
fi

# Cleanup
rm -f "$temp_file"

echo ""
echo "=================================================="
echo "  Tip: See EXCEPTION_HANDLING_GUIDE.md for help"
echo "=================================================="
