import datetime
import discord
import os

def log(message):
    now = datetime.datetime.utcnow()
    with open(f"log.txt","a+") as f:
        f.write(f"{now}: {message}\n")

def date_parse_utc_string(str_to_parse):
    """Parses UTC time into a more easily human readable form"""

    dt = datetime.datetime.strptime(str_to_parse, "%Y-%m-%d %H:%M:%S.%f")
    return dt.strftime("%b %d, %Y @ %H:%M:%S")

def date_parse_utc_datetime(str_to_parse):
    """Parses UTC time into a datetime object"""

    return datetime.datetime.strptime(str_to_parse, "%Y-%m-%d %H:%M:%S.%f")
    
def parse_string_timedelta_to_datetime(str_to_parse):
    """Parses an input in the format <day> day[s] <hour> hour[s] <minute> minute[s] <second> second[s] where every time field is optional but at least one is required
    Returns None if the parse fails
    """

    dt = None

    frags = str_to_parse.split(" ")
    vals = [0, 0, 0, 0]
    parse_formatter_string = ""

    print(frags)
    try:
        if len(frags) > 1:
            if frags[1] == "day":
                parse_formatter_string += "%d day"
                vals.insert(0, int(frags[0]))
                frags.pop(1)
                frags.pop(0)
            elif frags[1] == "days":
                parse_formatter_string += "%d days"
                vals.insert(0, int(frags[0]))
                frags.pop(1)
                frags.pop(0)

            if len(frags) > 1:
                if frags[1] == "hour":
                    parse_formatter_string += "%H hour"    
                    vals.insert(1, int(frags[0]))
                    frags.pop(1)
                    frags.pop(0)
                elif frags[1] == "hours":
                    parse_formatter_string += "%H hours"    
                    vals.insert(1, int(frags[0]))
                    frags.pop(1)
                    frags.pop(0)

                if len(frags) > 1:
                    if frags[1] == "minute":
                        parse_formatter_string += "%M minute"        
                        vals.insert(2, int(frags[0]))
                        frags.pop(1)
                        frags.pop(0)
                    elif frags[1] == "minutes":
                        parse_formatter_string += "%M minutes"        
                        vals.insert(2, int(frags[0]))
                        frags.pop(1)
                        frags.pop(0)

                    if len(frags) > 1:
                        if frags[1] == "second":
                            parse_formatter_string += "%S second"            
                            vals.insert(3, int(frags[0]))
                            frags.pop(1)
                            frags.pop(0)
                        elif frags[1] == "seconds":
                            parse_formatter_string += "%S seconds"            
                            vals.insert(3, int(frags[0]))
                            frags.pop(1)
                            frags.pop(0)
    except:
        return None

    if parse_formatter_string == "":
        return None

    if len(frags) != 0:
        return None

    dt = datetime.datetime.utcnow() + datetime.timedelta(days=vals[0], seconds=vals[3], minutes=vals[2], hours=vals[1])

    return dt

def get_channel_type(channel):
    if type(channel) is discord.TextChannel:
        return "Text"
    elif type(channel) is discord.VoiceChannel:
        return "Voice"
    elif type(channel) is discord.CategoryChannel:
        return "Category"
    else:
        return None

def mapFromTo(val, min_in, max_in, min_out, max_out):
    return (val - min_in) / (max_in - min_in) * (max_out - min_out) + min_out

def constrain(val, low, high):
    return low if val < low else high if val > high else val