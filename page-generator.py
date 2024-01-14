#!/usr/bin/env python3
import lib
from collections import defaultdict
import pickle


def embed_link(asn, cls="unknown"):
    file = open("classification", "rb")
    class_dict = pickle.load(file)
    if asn in class_dict:
        cls = class_dict[asn]
    return f"<a href='{asn}.html' class={cls}>{asn}   </a> |"

def create_index():
    file = open("classification", "rb")
    class_dict = pickle.load(file)

    with open("index.html", "w") as index_f:
        index_f.write('<!DOCTYPE html>\n')
        index_f.write('<html>\n')
        index_f.write('<head>\n')
        index_f.write('<title>My Python-generated HTML</title>\n')
        index_f.write('<style>\n')
        index_f.write('       .title-container {')
        index_f.write('           display: inline-block;')
        index_f.write('           vertical-align: top;')
        index_f.write('           /* Align titles at the top */')
        index_f.write('           margin-right: 20px;')
        index_f.write('           /* Adjust the margin as needed */')
        index_f.write('        }')
        index_f.write('</style>\n')


        index_f.write('<link rel="stylesheet" type="text/css" href="styles.css">')
        index_f.write('</head>\n')
        index_f.write('<body>\n')

        index_f.write("<div class='title-container''>")
        index_f.write(f'<h3>Drop-Invalid</h3><br>')
        for asn in class_dict:
            if class_dict[asn] == "drop-invalid":
                index_f.write(f"<a href='{asn}.html'>{asn}  </a>")
                index_f.write("<br>")
        index_f.write("</div>")

        index_f.write("<div class='title-container''>")
        index_f.write(f'<h3>Ignore-ROA</h3><br>')
        for asn in class_dict:
            if class_dict[asn] == "ignore-roa":
                index_f.write(f"<a href='{asn}.html'>{asn}  </a>")
                index_f.write("<br>")
        index_f.write("</div>")

        index_f.write("<div class='title-container''>")
        index_f.write(f'<h3>Prefer-Valid</h3><br>')
        for asn in class_dict:
            if class_dict[asn] == "prefer-valid":
                index_f.write(f"<a href='{asn}.html'>{asn}  </a>")
                index_f.write("<br>")
        index_f.write("</div>")

        index_f.write("<div class='title-container''>")
        index_f.write(f'<h3>Prefer-Valid or Ignore-ROA</h3><br>')
        for asn in class_dict:
            if class_dict[asn] == "prefer-ignore":
                index_f.write(f"<a href='{asn}.html'>{asn}  </a>")
                index_f.write("<br>")
        index_f.write("</div>")


        index_f.write(f'<h3>Unknown</h3><br>')
        for asn in class_dict:
            if class_dict[asn] == "unknown":
                index_f.write(f"<a href='{asn}.html'>{asn}  </a>")
                index_f.write("<br>")
        index_f.write("</div>")

        index_f.write('</body>')
        index_f.write('</html>')

def create_html():
    file = open("new_p0", "rb")
    new0 = pickle.load(file)

    file = open("new_p1", "rb")
    new1 = pickle.load(file)

    file = open("new_p2", "rb")
    new2 = pickle.load(file)

    file = open("new_p3", "rb")
    new3 = pickle.load(file)

    file = open("old_p0", "rb")
    old0 = pickle.load(file)

    for asn in new0:  # concatenar asns com todas as entradas ou nao, pensar melhor
        with open(f"{asn}.html", "w+") as f:
            # Write HTML content to the file
            f.write("<!DOCTYPE html>\n")
            f.write("<html>\n")
            f.write("<head>\n")
            f.write("<title>My Python-generated HTML</title>\n")
            f.write('<link rel="stylesheet" type="text/css" href="styles.css">')
            f.write("</head>\n")
            f.write("<body>\n")


            f.write(f"<h2>Announcements</h2>\n")
            f.write(
                f"<h3>P1: </h3> Short from BadSite and Long from GoodSite, no ROA (pfx: 204.9.170.0/24)<br>\n"
            )
            f.write(f"<a href='{asn}.html'>{asn}: </a>")
            for entry in old0[asn]:
                f.write(embed_link(entry))
            f.write("<br>\n")

            f.write(
                f"<h3>P2: </h3> Short from BadSite, no ROA (pfx: 138.185.228.0/24)<br>\n"
            )
            f.write(f"<a href='{asn}.html'>{asn}: </a>")
            for entry in new0[asn]:
                f.write(embed_link(entry))
            f.write("<br>\n")

            f.write(f"<h3>P3: </h3> Long from GoodSite, no ROA (pfx: 138.185.231.0/24)<br>\n")
            f.write(f"<a href='{asn}.html'>{asn}: </a>")
            for entry in new3[asn]:
                f.write(embed_link(entry))
            f.write("<br>\n")

            f.write(
                f"<h3>P4: </h3> Short from BadSite, invalid (pfx: 138.185.229.0/24)<br>\n"
            )
            f.write(f"<a href='{asn}.html'>{asn}: </a>")
            for entry in new1[asn]:
                f.write(embed_link(entry))
            f.write("<br>\n")
            ####
            #f.write(f"<h2>Old</h2>\n")
            f.write(f"<h3>P5: </h3> Short and invalid from BadSite, Long and valid from GoodSite (pfx: 138.185.230.0/24)<br>\n")
            f.write(f"<a href='{asn}.html'>{asn}: </a>")
            for entry in new2[asn]:
                f.write(embed_link(entry))
            f.write("<br>\n")
            f.write("</body>\n")
            f.write("</html>\n")


create_index()
create_html()
