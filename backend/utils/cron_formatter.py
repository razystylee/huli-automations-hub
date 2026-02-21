"""
Cron Expression Formatter

Converts Cron expressions to human-readable Portuguese format.
"""

from typing import Optional


class CronFormatter:
    """Convert cron expressions to readable Portuguese format"""

    DAYS_OF_WEEK = {
        "0": "domingo",
        "1": "segunda-feira",
        "2": "terça-feira",
        "3": "quarta-feira",
        "4": "quinta-feira",
        "5": "sexta-feira",
        "6": "sábado",
    }

    @staticmethod
    def format_cron(cron_expression: str) -> str:
        """
        Convert cron expression to readable Portuguese format

        Args:
            cron_expression: Cron expression (e.g., "0 6 * * *")

        Returns:
            Human-readable format in Portuguese (e.g., "Todos os dias às 06:00")
        """
        try:
            parts = cron_expression.split()
            if len(parts) < 5:
                return cron_expression  # Return as-is if invalid

            minute, hour, day, month, day_of_week = parts[0], parts[1], parts[2], parts[3], parts[4]

            # Handle common patterns
            # Every day at specific time
            if day == "*" and month == "*" and day_of_week == "*":
                return CronFormatter._format_daily(hour, minute)

            # Specific days of week
            if day == "*" and month == "*" and day_of_week != "*":
                return CronFormatter._format_weekly(hour, minute, day_of_week)

            # Every N hours
            if day == "*" and month == "*" and day_of_week == "*" and hour.startswith("*/"):
                return CronFormatter._format_hourly(hour, minute)

            # Fallback to generic format
            return cron_expression

        except Exception:
            return cron_expression

    @staticmethod
    def _format_daily(hour: str, minute: str) -> str:
        """Format daily recurring job"""
        try:
            hour_int = int(hour)
            minute_int = int(minute)
            return f"Todos os dias às {hour_int:02d}:{minute_int:02d}"
        except ValueError:
            return f"Todos os dias às {hour}:{minute}"

    @staticmethod
    def _format_weekly(hour: str, minute: str, day_of_week: str) -> str:
        """Format weekly recurring job"""
        try:
            hour_int = int(hour)
            minute_int = int(minute)
            time_str = f"{hour_int:02d}:{minute_int:02d}"

            # Handle single day or multiple days
            if "-" in day_of_week:
                # Range like 1-5 (Monday to Friday)
                start, end = day_of_week.split("-")
                start_day = CronFormatter.DAYS_OF_WEEK.get(start, start)
                end_day = CronFormatter.DAYS_OF_WEEK.get(end, end)
                return f"{start_day.capitalize()} a {end_day} às {time_str}"
            elif "," in day_of_week:
                # Multiple days like 1,3,5
                days = [CronFormatter.DAYS_OF_WEEK.get(d.strip(), d) for d in day_of_week.split(",")]
                days_str = ", ".join(d.capitalize() for d in days)
                return f"{days_str} às {time_str}"
            else:
                # Single day
                day_name = CronFormatter.DAYS_OF_WEEK.get(day_of_week, day_of_week)
                return f"Toda {day_name} às {time_str}"

        except ValueError:
            return f"Dia da semana {day_of_week} às {hour}:{minute}"

    @staticmethod
    def _format_hourly(hour: str, minute: str) -> str:
        """Format hourly recurring job"""
        try:
            hours = int(hour.split("/")[1])
            minute_int = int(minute)
            if minute_int == 0:
                return f"A cada {hours} hora{'s' if hours > 1 else ''}"
            else:
                return f"A cada {hours} hora{'s' if hours > 1 else ''} no minuto {minute_int}"
        except (ValueError, IndexError):
            return f"A cada {hour} horas"


def format_schedule_display(cron_expression: str) -> str:
    """
    Public function to format schedule for display

    Args:
        cron_expression: Cron expression string

    Returns:
        Human-readable schedule string in Portuguese
    """
    return CronFormatter.format_cron(cron_expression)
