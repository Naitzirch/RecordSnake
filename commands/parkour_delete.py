from helperfunctions import make_path
from helperfunctions import get_subkeys

def remove_parkour_record(parkour_db, users, path):
    keys = path.split('.')
    d = parkour_db
    for k in keys[:-1]: # iterate through the dot string
        d = d.get(k, {})
    parkour_record = d.get(keys[-1], {})
    record_holders = parkour_record.get("record_holders", [])
    for record_holder in record_holders:
        try:
            users[record_holder]["parkour_records"].remove(path) # remove record from holders in users db
        except ValueError:
            pass

    # remove from the parkour_db
    d.pop(keys[-1], None)


async def delete_impl(ctx, platform, mode, map_name, level, db_json, parkour_db_json, users):
    response_msg = "Record succesfully removed"
    parkour_db = parkour_db_json.data

    try:
        # Fetch record or record group if it exists
        record_group = parkour_db[platform][mode].get(map_name)
        if record_group is None:
            response_msg = "This map does not exist"
        else:
            if level:
                parkour_record = record_group.get(level)
                if not parkour_record:
                    response_msg = "This level does not exist"
                else:
                    remove_parkour_record(parkour_db, users, make_path(platform, mode, map_name, level))
                    db_json.save(indent=4)
                    parkour_db_json.save(indent=4)
            else:
                path = make_path(platform, mode, map_name)
                for level in get_subkeys(parkour_db, path):
                    remove_parkour_record(parkour_db, users, path+'.'+level)
                parkour_db[platform][mode].pop(map_name)
                db_json.save(indent=4)
                parkour_db_json.save(indent=4)
                response_msg = "Map and records succesfully removed"
    except Exception as e:
        response_msg = "Something went wrong. Please report the arguments you used in this command:\n"
        response_msg += f"`{platform}, {mode}, {map_name}, {level}`\n"
        response_msg += f"-# {e}"

    await ctx.respond(response_msg)