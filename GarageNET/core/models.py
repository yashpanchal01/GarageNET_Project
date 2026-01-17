from django.db import models

class JobCard(models.Model):
    customer_name = models.CharField(max_length=100)
    vehicle_number = models.CharField(max_length=20)
    issue = models.TextField()
    status = models.CharField(
        max_length=20,
        choices=[
            ('OPEN', 'Open'),
            ('IN_PROGRESS', 'In Progress'),
            ('DONE', 'Done')
        ],
        default='OPEN'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.customer_name
    

    class Part(models.Model):

          name = models.CharField(max_length=100)
          quantity = models.IntegerField()
          price = models.IntegerField()
          def __str__(self):
                return self.name    