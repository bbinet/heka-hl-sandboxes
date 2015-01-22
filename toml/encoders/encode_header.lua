require "string"
require "os"

function process_message()
    local data = os.date("%y%m%d %X", read_message('Timestamp')/1e9)
    data = data .. ' ' .. read_message('Fields[uuid]')
    data = data .. ' ' .. read_message('Fields[hostname]')
    data = data .. ' ' .. read_message('Fields[type]')
    data = data .. ' ' .. 0 ..':' .. read_message('Fields[version]')
    data = '[' .. data .. ']' .. read_message('Fields[log]') .. '\n'

    inject_payload('txt', 'log_parse', string.format(data))

    return 0
end
