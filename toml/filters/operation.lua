require "circular_buffer"

local agg = read_config('aggregation') or 'avg'
local sec_per_row = read_config('sec_per_row') or 5
local nb_rows = read_config('nb_rows') or 10
local next_sandbox = read_config('type_output') or 'output'
local nb_columns = 1
local cbufs = { }
local uuid = nil
local masterController = nil

function init_cbuf(name)
    cb = circular_buffer.new(nb_rows, nb_columns, sec_per_row)
    cb:set_header(1, name, 'count', 'none')
    cbufs[name] = cb

    return cb
end

function process_message()
    local ts    = read_message('Timestamp')
    uuid = read_message('Fields[uuid]')
    masterController = read_message('Fields[masterController]')
    local name  = read_message('Fields[name]')
    local value = read_message('Fields[value]')

    local cb = cbufs[name]
    if not cb then cb = init_cbuf(name) end
    cb:set(ts, 1, value)

    return 0
end

function timer_event(ns)
    for key, cb in pairs(cbufs) do
	local value = cb:compute(agg, 1)
        local data = {
            Type    = next_sandbox,
	    Timestamp = ns,
            Payload = ns .. ':' .. key .. ':' .. value,
            Fields  = {
		value = value,
	        uuid = uuid,
	        masterController = masterController,
		name  = key
	    }
        }

        inject_message(data)
	data = { }
    end
end
