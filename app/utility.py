from rdflib import RDF, RDFS, XSD, Literal
from vivo_namespace import VIVO
from numbers import Number
from SPARQLWrapper import SPARQLWrapper


def num_to_str(num):
    """
    Converts a number to a string.

    If the number is already a string, then just returns.
    """
    if isinstance(num, Number):
        return str(int(num))
    return num


def join_if_not_empty(items, sep=" "):
    """
    Joins a list of items with a provided separator.

    Skips an empty item.
    """
    joined = ""
    for item in items:
        if item and len(item) > 0:
            if joined != "":
                joined += sep
            joined += item
    return joined


months = ("January",
          "February",
          "March",
          "April",
          "May",
          "June",
          "July",
          "August",
          "September",
          "October",
          "November",
          "December")


def month_str_to_month_int(month_str):
    """
    Converts a month name to the corresponding month number.

    If already a number, returns the number.

    Also, tries to convert the string to a number.
    """
    if isinstance(month_str, Number):
        return month_str

    try:
        return int(month_str)
    except ValueError:
        pass

    return months.index(month_str)+1


def month_int_to_month_str(month_int):
    if isinstance(month_int, basestring):
        return month_int

    return months[month_int-1]


def add_date(date_uri, year, g, month=None, day=None, label=None):
    """
    Adds triples for a date.

    Return True if date was added.
    """
    #Date
    if year:
        g.add((date_uri, RDF.type, VIVO.DateTimeValue))
        #Day, month, and year
        if day and month:
            g.add((date_uri, VIVO.dateTimePrecision, VIVO.yearMonthDayPrecision))
            g.add((date_uri, VIVO.dateTime,
                   Literal("%s-%02d-%02dT00:00:00" % (
                       int(year), month_str_to_month_int(month), int(day)),
                       datatype=XSD.dateTime)))
            g.add((date_uri,
                   RDFS.label,
                   Literal(label or "%s %s, %s" % (month_int_to_month_str(month), num_to_str(day), num_to_str(year)))))
        #Month and year
        elif month:
            g.add((date_uri, VIVO.dateTimePrecision, VIVO.yearMonthPrecision))
            g.add((date_uri, VIVO.dateTime,
                   Literal("%s-%02d-01T00:00:00" % (
                       year, month_str_to_month_int(month)),
                       datatype=XSD.dateTime)))
            g.add((date_uri,
                   RDFS.label,
                   Literal(label or "%s %s" % (month, num_to_str(year)))))
        else:
            #Just year
            g.add((date_uri, VIVO.dateTimePrecision, VIVO.yearPrecision))
            g.add((date_uri, VIVO.dateTime,
                   Literal("%s-01-01T00:00:00" % (
                       year),
                       datatype=XSD.dateTime)))
            g.add((date_uri, RDFS.label, Literal(label or num_to_str(year))))
        return True
    return False


def add_date_interval(interval_uri, subject_uri, g, start_uri=None, end_uri=None):
    """
    Adds triples for a date interval.
    """
    if start_uri or end_uri:
        g.add((interval_uri, RDF.type, VIVO.DateTimeInterval))
        g.add((subject_uri, VIVO.dateTimeInterval, interval_uri))
        if start_uri:
            g.add((interval_uri, VIVO.start, start_uri))
        if end_uri:
            g.add((interval_uri, VIVO.end, end_uri))


def sparql_insert(graph, endpoint, username, password):
    #Need to construct query
    ns_lines = []
    triple_lines = []
    for line in graph.serialize(format="turtle").splitlines():
        if line.startswith("@prefix"):
            #Change from @prefix to PREFIX
            ns_lines.append("PREFIX" + line[7:-2])
        else:
            triple_lines.append(line)
    query = "\n".join(ns_lines)
    query += "\nINSERT DATA { GRAPH <http://vitro.mannlib.cornell.edu/default/vitro-kb-2> {\n"
    query += "\n".join(triple_lines)
    query += "\n}}"
    sparql = SPARQLWrapper(endpoint)
    sparql.addParameter("email", username)
    sparql.addParameter("password", password)
    sparql.setQuery(query)
    sparql.setMethod("POST")
    sparql.query()
