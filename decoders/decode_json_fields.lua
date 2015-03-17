require "cjson"

local type_output = read_config('type_output') or error('you must initialize "type_output" option')

function process_message()
    local fields = cjson.decode(read_message('Payload'))
    if type(fields) ~= "table" then
        return -1, "invalid json"
    end

    inject_message({
        Type = type_output,
        Fields = fields
    })

    return 0
end
