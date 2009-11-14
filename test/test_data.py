# -*- coding: utf-8 -*-
"""test data for tomtom"""

expected_list = \
"""2009-10-20 | addressbook  (pim)
2009-10-20 | TODO-list  (reminders)
2009-10-14 | Bash  (reminders)
2009-10-11 | dell 750  (projects)
2009-10-07 | python-work  (projects)
2009-10-05 | TDD  (reminders)
2009-10-04 | OpenSource Conference X  (conferences)
2009-10-04 | business cards  (pim)
2009-10-03 | japanese  (reminders)
2009-10-02 | Webpidgin  (projects)"""

list_appendix = \
"""2009-09-27 | conquer the world  (projects)
2009-09-21 | recipies  (pim)
2009-09-20 | R&D  (reminders)"""

search_results = \
"""addressbook : 35 : John Doe (cell) - 555-5512
business cards : 21 : John Doe Sr. (office) - 555-5534"""

specific_search_results = \
"""dell 750 : 12 : Install python 2.5
python-work : 2 : to use a python buildbot for automatic bundling
OpenSource Conference X : 120 : Presentation: Python by all means"""

expected_note_content = \
"""TODO

Build unit tests for tomtom
Chew up some gum
Play pool with the queen of england"""

URL_list =  [
    "note://tomboy/b332eb31-8139-4351-9f5d-738bf64ce172",
    "note://tomboy/30ae533a-2789-4789-a409-16a6f65edf54",
    "note://tomboy/4652f914-85dd-487d-b614-188242f52241",
    "note://tomboy/5815160c-7143-4c56-9c5f-007acca375ad",
    "note://tomboy/89277e3b-bdb7-4cfe-a42c-7c8b207370fd",
    "note://tomboy/bece0d43-19ba-41cf-92b5-7b30a5411a0c",
    "note://tomboy/1a1994da-1b98-41d2-8eab-26e8581fc391",
    "note://tomboy/21612e71-e2ec-4afb-82bb-7e663e58e88c",
    "note://tomboy/8dd14cf8-4766-4122-8178-192cdc0e99dc",
    "note://tomboy/c0263232-c3b8-45a8-bfdc-7cb8ee4b2a5d",
    "note://tomboy/ea6f4c7f-1b82-4835-9aa2-2df002d788f4",
    "note://tomboy/461fb1a2-1e02-4447-8891-c3c6fcbb26eb",
    "note://tomboy/5df0fd74-cbdd-4cf3-bb08-7a7f09997afd",
    "note://tomboy/0045cd16-2977-456a-b790-9a256f5b2a71",
    "note://tomboy/ade154ac-9208-46fe-9355-a958d272a6c0",
    "note://tomboy/1632707b-e92c-4fca-9d62-4a41c7e8fb89",
    "note://tomboy/fd6fa06f-836c-48de-961b-86e31ebc0fb0",
]

#TODO change elements into note objects
full_list_of_notes = [
    "meuh",
]
