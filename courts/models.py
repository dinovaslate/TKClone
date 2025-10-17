from django.conf import settings
from django.db import models
from django.urls import reverse


class Court(models.Model):
    SURFACE_SYNTHETIC = 'synthetic'
    SURFACE_NATURAL = 'natural'
    SURFACE_CHOICES = (
        (SURFACE_SYNTHETIC, 'Synthetic'),
        (SURFACE_NATURAL, 'Natural'),
    )

    name = models.CharField(max_length=150)
    location = models.CharField(max_length=200)
    description = models.TextField()
    surface_type = models.CharField(max_length=20, choices=SURFACE_CHOICES)
    length_m = models.PositiveIntegerField()
    width_m = models.PositiveIntegerField()
    price_per_hour = models.DecimalField(max_digits=10, decimal_places=2)
    open_time = models.TimeField()
    close_time = models.TimeField()
    image = models.URLField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('name',)

    def __str__(self) -> str:  # pragma: no cover - simple representation
        return self.name

    def get_absolute_url(self) -> str:
        return reverse('courts:detail', args=[self.pk])


class MaintenanceBlock(models.Model):
    court = models.ForeignKey(Court, related_name='maintenance_blocks', on_delete=models.CASCADE)
    start_dt = models.DateTimeField()
    end_dt = models.DateTimeField()
    reason = models.CharField(max_length=200)

    class Meta:
        ordering = ('start_dt',)

    def __str__(self) -> str:  # pragma: no cover
        return f"{self.court.name} maintenance"


class FavoriteCourt(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='favorite_courts', on_delete=models.CASCADE)
    court = models.ForeignKey(Court, related_name='favorited_by', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'court')
        ordering = ('-created_at',)

    def __str__(self) -> str:  # pragma: no cover
        return f"{self.user} -> {self.court}"
