from django.dispatch import receiver
from django.db.models.signals import post_save

from models import Regret


@receiver(post_save, sender=Regret)
def update_checklist_score(sender, instance, **kwargs) -> None:
    checklist = instance.checklist
    
    # Dont allow scores to be updated if the checklist is already completed
    if checklist.completed:
        return
    
    # Recalculate checklist score, considering all regrets
    regrets = checklist.checklist_regrets
    checklist.score = sum(regret.success for regret in regrets) / regrets.count()
    checklist.save()
