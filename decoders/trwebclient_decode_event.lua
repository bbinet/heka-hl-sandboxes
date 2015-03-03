require "cjson"

local type_output = read_config('type_output') or error('you must initialize "type_output" option')

function process_message()
    local payload = cjson.decode(read_message('Payload'))

    inject_message({
        Type = type_output,
        Timestamp = timestamp,
        Payload = log,
        Fields = {
            log = payload.log,
            msg = payload.msg
        }
    })

    return 0
end
