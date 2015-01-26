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
    data = table.concat(data, " ")
    data = '[' .. data .. ']' .. read_message('Fields[log]') .. '\n'

    inject_payload('txt', 'log_parse', string.format(data))

    return 0
end
