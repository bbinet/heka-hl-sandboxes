require "string"
require "table"
require "os"

function process_message()
    local data = { }
    data[#data+1] = os.date("%X", read_message('Timestamp')/1e9)
    data[#data+1] = read_message('Timestamp')
    data[#data+1] = read_message('Fields[uuid]')
    data[#data+1] = read_message('Fields[hostname]')
    data[#data+1] = read_message('Fields[type]') .. ':' .. read_message('Fields[encoder_version]')

    inject_payload('txt', 'log_parse', '[' .. table.concat(data, " ") .. ']' .. read_message('Payload') .. '\n')

    return 0
end
