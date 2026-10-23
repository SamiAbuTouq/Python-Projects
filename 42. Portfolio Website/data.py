"""All portfolio content lives here. Edit this file, not the templates.
Source: https://sami-abu-touq.pages.dev/"""

PROFILE = {
    "name": "Sami Abu Touq",
    "headline": "Give me a tangled, messy puzzle and I’m in my element.",
    "sub": ("Computer Science graduate from PSUT (GPA 84.7%) and former CRM Developer Intern at "
            "Dynamics Innovations Software. I turn complex engineering problems into clean, reliable "
            "and scalable software."),
    "status": "Joining Optimiza on 25 Oct 2026 as Associate ERP Solutions Specialist (CRM – CX).",
    "email": "sami.a.touq@gmail.com",
    "location": "Amman, Jordan",
    "code_stack": ["Python", "C#", "JavaScript", "Dynamics 365", "Dataverse"],  # shown in the hero code card
    "links": [
        ("GitHub", "https://github.com/SamiAbuTouq"),
        ("LinkedIn", "https://www.linkedin.com/in/sami-abu-touq/"),
    ],
}

# Featured projects (full rows)
PROJECTS = [
    {
        "name": "Property Rental Management System",
        "what": ("Built on Microsoft Dynamics 365 CRM during my internship: contract, unit and invoice management. "
                 "C# plugins, JavaScript, custom workflows and REST APIs automate contract activation, validation "
                 "and invoice generation, and the Dataverse security model enforces role-based access."),
        "stack": ["Dynamics 365", "Dataverse", "C# plugins", "JavaScript", "REST APIs"],
        "link": "",
    },
    {
        "name": "Smart University Timetabling System",
        "what": ("My graduation project for PSUT. It solves constraint satisfaction and multi-objective optimization "
                 "with a Grey Wolf Optimizer, and includes What-If scenarios and an analytics dashboard to compare "
                 "alternative schedules in isolated sandboxes."),
        "stack": ["Grey Wolf Optimizer", "NestJS", "Next.js", "PostgreSQL", "Prisma", "Python"],
        "link": "",
    },
    {
        "name": "Company website for Sanbal Mall",
        "what": ("A responsive website for a client, with Sanity as a headless CMS so products and content can be "
                 "managed without code changes."),
        "stack": ["Next.js", "Sanity CMS"],
        "link": "",
    },
    {
        "name": "Python automation and backend projects",
        "what": "More than 40 projects: automation bots, authentication systems and web apps using Python, APIs and databases.",
        "stack": ["Python", "APIs", "Databases"],
        "link": "https://github.com/SamiAbuTouq/Python-Projects",
    },
]

MORE_PROJECTS = [
    {"name": "Flutter mobile applications (6 apps)",
     "what": "A chat system, an expense tracker and a geolocation app, among others.",
     "stack": ["Flutter", "Dart", "Firebase", "REST APIs"],
     "link": "https://github.com/SamiAbuTouq/Flutter-Udemy"},
    {"name": "Connectify",
     "what": "A Flutter app that connects service providers with service requesters for task-based job assignments.",
     "stack": ["Flutter"],
     "link": "https://github.com/SamiAbuTouq/Connectify"},
    {"name": "Pharmacy Management System",
     "what": "An OOP course project using classes, encapsulation, inheritance and polymorphism.",
     "stack": ["C++"],
     "link": "https://github.com/SamiAbuTouq/Pharmacy-Project"},
    {"name": "DART: Digital Access to Remarkable Treasures",
     "what": "A web application built for web development coursework.",
     "stack": ["PHP", "MySQL", "HTML", "CSS"],
     "link": "https://github.com/SamiAbuTouq/DART-Project"},
    {"name": "Assembly project",
     "what": "A low-level project covering computer architecture, registers and memory management.",
     "stack": ["Assembly"],
     "link": "https://github.com/SamiAbuTouq/Assembly-Project"},
    {"name": "Software engineering project",
     "what": "UML diagrams modelling system architecture, behaviour and interactions.",
     "stack": ["UML"],
     "link": "https://github.com/SamiAbuTouq/SE-Project"},
]

SKILLS = {
    "Programming languages": ["C#", "C++", "C", "JavaScript", "Dart", "PHP", "Python"],
    "Technologies": ["Dynamics 365", "Dataverse", ".NET Framework", "ASP.NET Web API", "REST APIs", "HTML", "CSS",
                     "Flutter", "SQL", "PostgreSQL", "Firebase", "Prisma"],
    "Tools and AI": ["Git", "GitHub", "Cursor", "Antigravity"],
    "Spoken languages": ["Arabic (native)", "English (professional working)"],
}

PATH = [
    ("Sep 2021 – Jul 2022", "Jordanian high school diploma (Tawjihi) at Omam Schools, GPA 84.8%."),
    ("Sep 2022", "Started a Bachelor of Computer Science at Princess Sumaya University for Technology."),
    ("Oct 2024", "IEEE-XTREME 18: top 31.3% in the world with almost 9,000 participants."),
    ("Nov 2024", "JCPC: ranked 37th out of 120 teams."),
    ("2024 – 2026", "Digital Logic Design lecturer: face-to-face lectures and recorded materials."),
    ("Jun 2026", "Graduated with a Bachelor of Computer Science, GPA 84.7%."),
    ("Jun – Aug 2026", "CRM Developer intern at Dynamics Innovations Software LLC, Amman."),
    ("Oct 2026", "Joining Optimiza as Associate ERP Solutions Specialist."),
]

CERTS = [
    {"name": "Intro to Machine Learning", "org": "Kaggle", "date": "Oct 2025", "link": ""},
    {"name": "Meta Front-End Developer Specialization", "org": "Meta (Coursera)", "date": "Jul 2025",
     "link": "https://www.coursera.org/account/accomplishments/specialization/SQOZQDD44DB7"},
    {"name": "AWS Academy Cloud Foundations", "org": "Amazon Web Services", "date": "Mar 2025",
     "link": "https://www.credly.com/badges/cbe38519-a170-4cfc-b027-9120dac8758c/linked_in_profile"},
    {"name": "Computer Network", "org": "Huawei", "date": "Mar 2025", "link": ""},
    {"name": "Flutter & Dart: The Complete Guide", "org": "Udemy", "date": "Feb 2025",
     "link": "https://www.udemy.com/certificate/UC-b48ca0d2-41cd-40d5-888b-d98707bce087/"},
]

VOLUNTEERING = [
    {"name": "Run Jordan", "when": "Oct 2024 – present", "what": "Helped organize and coordinate the Amman Marathon."},
    {"name": "Nahno platform", "when": "Apr 2020 – Oct 2023", "what": "Completed 24 hours of volunteer work in community activities and initiatives."},
]
