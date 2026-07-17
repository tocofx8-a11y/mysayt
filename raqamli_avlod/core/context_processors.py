from .models import ShowcaseCard


def showcase_cards(request):
    """
    Kirish (mehmon) sahifasidagi to'rtta ma'lumot tugmasini barcha
    shablonlarga taqdim etadi. Faqat tizimga kirmagan foydalanuvchilar
    uchun kerak, shuning uchun kirgan foydalanuvchilarda bekor qilinadi.
    """
    if getattr(request, 'user', None) and request.user.is_authenticated:
        return {}
    cards = {c.slot: c for c in ShowcaseCard.objects.all()}
    ordered = [cards[slot] for slot, _ in ShowcaseCard.Slot.choices if slot in cards]
    return {'showcase_cards': ordered}
