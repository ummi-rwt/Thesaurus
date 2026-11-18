from datetime import date, timedelta

START_EASE = 2.5
MIN_EASE = 1.3


def next_state(repetitions, ease, interval, quality, today):
    """SM-2. Retourne (repetitions, ease, interval_jours, date_prochaine)."""
    if not 0 <= quality <= 5:
        raise ValueError("quality doit etre entre 0 et 5")
    if quality < 3:
        return 0, ease, 0, today
    if repetitions == 0:
        interval = 1
    elif repetitions == 1:
        interval = 6
    else:
        interval = round(interval * ease)
    ease = max(MIN_EASE, ease + 0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
    return repetitions + 1, ease, interval, today + timedelta(days=interval)
