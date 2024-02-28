from django.core.management.base import BaseCommand
from NewEra.models import Resource, Tag
# Import to read CSV
import csv
# Regex matching
import re

# POPULATE SCRIPT

class Command(BaseCommand):
    args = '<this func takes no args>'
    help = 'Run this script to create the resources and tags.'

    # Loads the tags and resources 
    def _create_tags_and_resources(self):

        # Open the CSV file
        with open('Northside PD Service Providers.csv', newline='') as csvfile:
            # Initialize a reader for the CSV
            reader = csv.reader(csvfile, delimiter=',')
            # Ignore the header row
            header = next(reader, None)
            # Loop through every row
            for row in reader:
                # Filter through tags and find the first one with a matching name
                tag = Tag.objects.all().filter(name=row[1]).first()

                # If the tag is not found, create it
                if (tag == None):
                    tag = Tag.objects.create(name=row[1])
                    tag.save()

                # Replace all non-numeric digits in the phone number
                phone_formatted = row[5].replace('(', '').replace(')', '').replace(' ', '').replace('-', '')

                # Split the phone nubmer on extension string
                phone_list = phone_formatted.split('ext.')
                # Check the size of the new list and set the extension if it exists
                if len(phone_list) > 1:
                    phone_extension = phone_list[1]
                else:
                    phone_extension = ''

                # Join the digits of the phone number together to create the string
                phone_formatted = ''.join(list(filter(str.isdigit, phone_list[0])))
                # Replace all non-numeric digits in the fax number 
                fax_formatted = row[6].replace('(', '').replace(')', '').replace(' ', '').replace('-', '')

                # Create a resource from the row columns and give it the tag
                r = Resource.objects.create(name=row[0], url=row[2], contact_name=row[3], contact_position=row[4], phone=phone_formatted, extension=phone_extension, fax_number=fax_formatted, contact_email=row[7], email=row[7], street=row[8], city=row[9], state=row[10], zip_code=row[11], street_secondary=row[12], description=row[13])
                r.tags.add(tag)
                r.save()
                
    def handle(self, *args, **options):
        self._create_tags_and_resources()
