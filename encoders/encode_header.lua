require "string"
require "table"
require "os"

function process_message()
    local data = {
        os.date("%X", read_message('Timestamp')/1e9),
        read_message('Fields[hostname]'),
        read_message('Fields[uuid]'),
        string.format("%d", read_message('Timestamp')),
        read_message('Fields[encoder_type]') .. ':' .. read_message('Fields[encoder_version]')
    }

    for k, v in pairs(data) do
        if v == nil then
            return -1, "data[" .. k .. "] can't be nil"
        end
    end

    inject_payload('txt', 'log_encode', '[' .. table.concat(data, " ") .. '] ' .. read_message('Payload') .. '\n')

    return 0
end
