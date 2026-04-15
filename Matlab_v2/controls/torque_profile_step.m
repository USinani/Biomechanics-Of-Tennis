function u = torque_profile_step(t, params)
%TORQUE_PROFILE_STEP Constant torques after per-joint onsets (N*m).
c = params.control;
u = [0; 0];
if t >= c.shoulder_onset
    u(1) = c.shoulder_tau;
end
if t >= c.elbow_onset
    u(2) = c.elbow_tau;
end
u = u(:);
end
