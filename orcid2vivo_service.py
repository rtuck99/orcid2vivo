from flask import Flask, render_template, request, session, Response, flash
import argparse
import json
import orcid2vivo
import app.utility as utility

app = Flask(__name__)
def_format = None
def_endpoint = None
def_username = None
def_password = None
def_namespace = None
def_person_class = "Person"
def_skip_person = False
def_output = "serialize"
def_output_html = True
def_output_profile = False

content_types = {
    "xml": "application/rdf+xml",
    "n3": "text/rdf+n3",
    "turtle": "application/x-turtle",
    "nt": "text/plain",
    "pretty-xml": "application/rdf+xml",
    "trix": "application/rdf+xml"
}

@app.route('/', methods=["GET"])
def crosswalk_form(rdf=None, orcid_profile=None):
    return render_template("crosswalk_form.html",
                           format=session.get("format") or def_format,
                           endpoint=session.get("endpoint") or def_endpoint,
                           username=session.get("username") or def_username,
                           password=session.get("password") or def_password,
                           namespace=session.get("namespace") or def_namespace,
                           person_class=session.get("person_class") or def_person_class,
                           skip_person=session.get("skip_person") or def_skip_person,
                           output=session.get("output") or def_output,
                           output_html=session.get("output_html") or def_output_html,
                           output_profile=session.get("output_profile") or def_output_profile,
                           rdf=rdf,
                           orcid_profile=json.dumps(orcid_profile, indent=3) if orcid_profile else None)

@app.route('/', methods=["POST"])
def crosswalk():
    session["format"] = request.form.get("format")
    session["endpoint"] = request.form.get("endpoint")
    session["username"] = request.form.get("username")
    session["password"] = request.form.get("password")
    person_class = request.form.get("person_class")
    session["person_class"] = person_class
    session["skip_person"] = True if "skip_person" in request.form else False
    session["output"] = request.form.get("output")
    session["output_html"] = True if "output_html" in request.form else False
    session["output_profile"] = True if "output_profile" in request.form else False

    (g, p) = orcid2vivo.crosswalk(request.form['orcid_id'],
                                  person_class=person_class if person_class != "Person" else None,
                                  skip_person=True if "skip_person" in request.form else False)

    if "output" in request.form and request.form["output"] == "vivo":
        utility.sparql_insert(g, request.form["endpoint"], request.form["username"], request.form["password"])
        flash("Loaded to VIVO")
        return crosswalk_form()
    else:
        #Serialize
        rdf = g.serialize(format=request.form['format'])
        if "output_html" in request.form or "output_profile" in request.form:
            return crosswalk_form(rdf=rdf if "output_html" in request.form else None,
                                  orcid_profile=p if "output_profile" in request.form else None)
        else:
            return Response(rdf, content_type=content_types[request.form['format']])


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--format", default="turtle", choices=["xml", "n3", "turtle", "nt", "pretty-xml", "trix"],
                        help="The RDF format for serializing. Default is turtle.")
    parser.add_argument("--endpoint", dest="endpoint",
                        help="Endpoint for SPARQL Update of VIVO instance,e.g., http://localhost/vivo/api/sparqlUpdate.")
    parser.add_argument("--username", dest="username", help="Username for VIVO root.")
    parser.add_argument("--password", dest="password",
                        help="Password for VIVO root.")
    parser.add_argument("--namespace", default="http://vivo.mydomain.edu/individual/",
                        help="VIVO namespace. Default is http://vivo.mydomain.edu/individual/.")
    parser.add_argument("--person-class", dest="person_class",
                        choices=["FacultyMember", "FacultyMemberEmeritus", "Librarian", "LibrarianEmeritus",
                                 "NonAcademic", "NonFacultyAcademic", "ProfessorEmeritus", "Student"],
                        help="Class (in VIVO Core ontology) for a person. Default is a FOAF Person.")
    parser.add_argument("--skip-person", dest="skip_person", action="store_true",
                        help="Skip adding triples declaring the person and the person's name.")
    parser.add_argument("--debug", action="store_true")
    parser.add_argument("--port", type=int, default="5000", help="The port the service should run on. Default is 5000.")

    #Parse
    args = parser.parse_args()

    def_format = args.format
    def_endpoint = args.endpoint
    def_username = args.username
    def_password = args.password
    def_namespace = args.namespace
    def_person_class = args.person_class
    def_skip_person = args.skip_person


    app.debug = args.debug
    app.secret_key = "orcid2vivo"
    app.run(host="0.0.0.0", port=args.port)