require "string"
require "table"

local uuid = read_config('uuid') or error ('you must initialize "uuid" option')
local hostname = read_config('hostname') or error ('you must initialize "hostname" option')

function process_message()
    local timestamp = read_message('Timestamp')
    if timestamp == nil then
        return -1, "Timestamp can't be nil"
    end
    local timestr = string.format("%d", timestamp/1e9)

    while true do
	typ, key, value = read_next_field()
	if not typ then break end
        -- exclude bytes and internal fields starting with '_' char
	if typ ~= 1 and key:match'^(.)' ~= '_' then
            add_to_payload(table.concat({
                table.concat({uuid, hostname, key}, '.'),
                value,
                timestr
            }, " ") .. '\n')
	end
    end

    inject_payload('txt', 'encode_carbon')

    return 0
end
