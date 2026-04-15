function validate_params(params)
%VALIDATE_PARAMS Check required fields for run_swing_sim / batch runs.
req_top = {'dt', 't_end', 'q0', 'qd0', 'physics', 'control', 'output_root'};
for i = 1:numel(req_top)
    if ~isfield(params, req_top{i})
        error('validate_params:missing', 'params missing field: %s', req_top{i});
    end
end
phys = params.physics;
req_p = {'l1', 'l2', 'm1', 'm2', 'lc1', 'lc2', 'I1', 'I2', 'g'};
for i = 1:numel(req_p)
    if ~isfield(phys, req_p{i})
        error('validate_params:physics', 'params.physics missing: %s', req_p{i});
    end
end
if numel(params.q0) ~= 2 || numel(params.qd0) ~= 2
    error('validate_params:ic', 'q0 and qd0 must be 2x1');
end
if ~isfield(params.control, 'type')
    error('validate_params:control', 'params.control.type required');
end
end
