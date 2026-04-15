function u = torque_profile_piecewise(t, params)
%TORQUE_PROFILE_PIECEWISE Hold torque constant between knot times (last value holds).
c = params.control;
times = c.piecewise_times(:);
taus = c.piecewise_taus;
if isempty(times) || isempty(taus)
    u = [0; 0];
    return;
end
if size(taus, 2) ~= 2
    error('torque_profile_piecewise:taus', 'piecewise_taus must be Nx2');
end
idx = find(t >= times, 1, 'last');
if isempty(idx)
    u = [0; 0];
else
    u = taus(idx, :)';
end
end
