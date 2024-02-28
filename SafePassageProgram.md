I wanted to put together a list of things of note and ideas for enhancements in the future. These are just ideas that have mostly hit me while I was trying to think about how an SDET might have tested the system, or how a UX Designer would enhance it.
1. No data is deleted from the system. It is marked inactive (is_active boolean field in database)
2. When an Organization (School) is deleted/inactivated, it does NOT cascade down to related User/Safe Passage Coordinator records.
3. When a Safe Passage Coordinator is deleted/inactivated, it does NOT cascade down to the related student records
4. When a student is made inactive, it does NOT cascade down to the related Weekly Updates or Quarterly Updates
5. The dashboard graphs report only the active data
6. Students, Weekly Updates, and Quarterly Updates currently only have a filter based on data_created for the records.
    1. Add filter for "Student Name" on Weekly Update and Quarterly Update pages
    2. Add Filter for "Active Only"
7. There is no pagination of data, add this, and/or the filters above.
8. Date Created field exists in the database for each piece of data, but is not shown on page.
    1. Weekly Update may need this on page. If we have a student filter so that a Safe Passage Coordinator can limit view on a single student, they may want to see the date of that week (and ensure they are ordered properly)
9. What does next year look like? What data will need to be archived and how will that be done?