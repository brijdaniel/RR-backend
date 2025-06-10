from django.dispatch import receiver
from django.db.models.signals import post_save
import logging

from .models import Regret

logger = logging.getLogger(__name__)

@receiver(post_save, sender=Regret)
def update_checklist_score(sender, instance, **kwargs) -> None:
    logger.info(f"Signal triggered for Regret {instance.id}")
    checklist = instance.checklist
    
    # Don't allow scores to be updated if the checklist is already completed
    if checklist.completed:
        logger.info(f"Checklist {checklist.id} is completed, skipping score update")
        return
    
    # Recalculate checklist score, considering all regrets
    regrets = checklist.checklist_regrets.all()
    total_regrets = regrets.count()
    
    if total_regrets > 0:
        # Count incomplete tasks (where success is False)
        incomplete_regrets = sum(1 for regret in regrets if not regret.success)
        # Score is the ratio of incomplete tasks
        checklist.score = incomplete_regrets / total_regrets
        logger.info(f"Updated checklist {checklist.id} score to {checklist.score} ({incomplete_regrets}/{total_regrets} incomplete)")
        checklist.save()
    else:
        logger.info(f"No regrets found for checklist {checklist.id}")
