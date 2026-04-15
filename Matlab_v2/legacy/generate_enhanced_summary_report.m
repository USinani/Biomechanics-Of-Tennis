function generate_enhanced_summary_report(results, output_filename)
%GENERATE_ENHANCED_SUMMARY_REPORT Creates a comprehensive analysis report
%
% This function generates a detailed summary report of the tennis swing
% simulation results, including kinematic analysis, dynamic analysis,
% and performance metrics.
%
% Inputs:
%   results         - Structure containing simulation results:
%                     .time          - Time vector
%                     .params_2link  - Two-link model parameters
%                     .params_3link  - Three-link model parameters
%                     .two_link      - Two-link model results
%                     .three_link    - Three-link model results
%                     .ball          - Ball trajectory results (optional)
%   output_filename - (Optional) Output filename for the report
%                     Default: 'tennis_simulation_report.txt'
%
% Example:
%   results = load('tennis_simulation_results.mat');
%   generate_enhanced_summary_report(results.results);
%
% Author: PhD Research Model
% Date: 2024

%% Input Validation
if nargin < 1
    error('generate_enhanced_summary_report:NotEnoughInputs', ...
          ['Not enough input arguments.\n' ...
           'Usage: generate_enhanced_summary_report(results)\n' ...
           'Run "help generate_enhanced_summary_report" for more information.']);
end

if nargin < 2 || isempty(output_filename)
    output_filename = 'tennis_simulation_report.txt';
end

% Validate results structure
if ~isstruct(results)
    error('generate_enhanced_summary_report:InvalidInput', ...
          'results must be a structure');
end

%% Extract Data from Results
% Check for different swing types if present
if isfield(results, 'flat') || isfield(results, 'topspin') || isfield(results, 'slice')
    % Multiple swing types
    swing_types = fieldnames(results);
    multi_swing = true;
else
    % Single simulation result
    swing_types = {'single'};
    temp_results.single = results;
    results = temp_results;
    multi_swing = false;
end

%% Open Output File
fid = fopen(output_filename, 'w');
if fid == -1
    warning('Could not create output file. Printing to console instead.');
    fid = 1;  % stdout
end

%% Print Report Header
fprintf(fid, '================================================================================\n');
fprintf(fid, '             TENNIS SWING BIOMECHANICS SIMULATION REPORT\n');
fprintf(fid, '================================================================================\n');
fprintf(fid, 'Generated: %s\n', datestr(now, 'yyyy-mm-dd HH:MM:SS'));
fprintf(fid, '\n');

%% Process Each Swing Type
for s = 1:length(swing_types)
    swing_name = swing_types{s};
    swing_data = results.(swing_name);
    
    if multi_swing
        fprintf(fid, '\n--------------------------------------------------------------------------------\n');
        fprintf(fid, '                    SWING TYPE: %s\n', upper(swing_name));
        fprintf(fid, '--------------------------------------------------------------------------------\n');
    end
    
    %% 1. Simulation Parameters
    fprintf(fid, '\n1. SIMULATION PARAMETERS\n');
    fprintf(fid, '------------------------\n');
    
    if isfield(swing_data, 'time')
        time = swing_data.time;
        fprintf(fid, '   Simulation duration: %.3f s\n', time(end) - time(1));
        fprintf(fid, '   Time step: %.4f s\n', time(2) - time(1));
        fprintf(fid, '   Number of samples: %d\n', length(time));
    end
    
    %% 2. Anthropometric Parameters
    fprintf(fid, '\n2. MODEL PARAMETERS\n');
    fprintf(fid, '-------------------\n');
    
    if isfield(swing_data, 'params_2link')
        p = swing_data.params_2link;
        fprintf(fid, '\n   Two-Link Model:\n');
        fprintf(fid, '   ---------------\n');
        if isfield(p, 'l1'), fprintf(fid, '   Upper arm length:     %.3f m\n', p.l1); end
        if isfield(p, 'l2'), fprintf(fid, '   Forearm+racket length: %.3f m\n', p.l2); end
        if isfield(p, 'm1'), fprintf(fid, '   Upper arm mass:       %.3f kg\n', p.m1); end
        if isfield(p, 'm2'), fprintf(fid, '   Forearm+racket mass:  %.3f kg\n', p.m2); end
        if isfield(p, 'I1'), fprintf(fid, '   Upper arm inertia:    %.4f kg*m^2\n', p.I1); end
        if isfield(p, 'I2'), fprintf(fid, '   Forearm+racket inertia: %.4f kg*m^2\n', p.I2); end
    end
    
    if isfield(swing_data, 'params_3link')
        p = swing_data.params_3link;
        fprintf(fid, '\n   Three-Link Model:\n');
        fprintf(fid, '   -----------------\n');
        if isfield(p, 'l1'), fprintf(fid, '   Upper arm length: %.3f m\n', p.l1); end
        if isfield(p, 'l2'), fprintf(fid, '   Forearm length:   %.3f m\n', p.l2); end
        if isfield(p, 'l3'), fprintf(fid, '   Racket length:    %.3f m\n', p.l3); end
        if isfield(p, 'm1'), fprintf(fid, '   Upper arm mass:   %.3f kg\n', p.m1); end
        if isfield(p, 'm2'), fprintf(fid, '   Forearm mass:     %.3f kg\n', p.m2); end
        if isfield(p, 'm3'), fprintf(fid, '   Racket mass:      %.3f kg\n', p.m3); end
    end
    
    %% 3. Kinematic Analysis
    fprintf(fid, '\n3. KINEMATIC ANALYSIS\n');
    fprintf(fid, '---------------------\n');
    
    % Two-link model kinematics
    if isfield(swing_data, 'two_link')
        tl = swing_data.two_link;
        fprintf(fid, '\n   Two-Link Model:\n');
        
        if isfield(tl, 'theta')
            theta = tl.theta;
            fprintf(fid, '   Joint Angle Ranges (degrees):\n');
            fprintf(fid, '     Shoulder: %.1f to %.1f (range: %.1f)\n', ...
                    rad2deg(min(theta(:,1))), rad2deg(max(theta(:,1))), ...
                    rad2deg(max(theta(:,1)) - min(theta(:,1))));
            fprintf(fid, '     Elbow:    %.1f to %.1f (range: %.1f)\n', ...
                    rad2deg(min(theta(:,2))), rad2deg(max(theta(:,2))), ...
                    rad2deg(max(theta(:,2)) - min(theta(:,2))));
        end
        
        if isfield(tl, 'theta_dot')
            theta_dot = tl.theta_dot;
            fprintf(fid, '   Peak Joint Velocities (deg/s):\n');
            fprintf(fid, '     Shoulder: %.1f\n', rad2deg(max(abs(theta_dot(:,1)))));
            fprintf(fid, '     Elbow:    %.1f\n', rad2deg(max(abs(theta_dot(:,2)))));
        end
        
        if isfield(tl, 'racket_speed')
            racket_speed = tl.racket_speed;
            [max_speed, max_idx] = max(racket_speed);
            fprintf(fid, '   Racket Head Speed:\n');
            fprintf(fid, '     Maximum: %.2f m/s (%.1f km/h)\n', max_speed, max_speed * 3.6);
            if isfield(swing_data, 'time')
                fprintf(fid, '     Time at max speed: %.3f s\n', swing_data.time(max_idx));
            end
        end
    end
    
    % Three-link model kinematics
    if isfield(swing_data, 'three_link')
        tl3 = swing_data.three_link;
        fprintf(fid, '\n   Three-Link Model:\n');
        
        if isfield(tl3, 'theta')
            theta = tl3.theta;
            fprintf(fid, '   Joint Angle Ranges (degrees):\n');
            fprintf(fid, '     Shoulder: %.1f to %.1f (range: %.1f)\n', ...
                    rad2deg(min(theta(:,1))), rad2deg(max(theta(:,1))), ...
                    rad2deg(max(theta(:,1)) - min(theta(:,1))));
            fprintf(fid, '     Elbow:    %.1f to %.1f (range: %.1f)\n', ...
                    rad2deg(min(theta(:,2))), rad2deg(max(theta(:,2))), ...
                    rad2deg(max(theta(:,2)) - min(theta(:,2))));
            fprintf(fid, '     Wrist:    %.1f to %.1f (range: %.1f)\n', ...
                    rad2deg(min(theta(:,3))), rad2deg(max(theta(:,3))), ...
                    rad2deg(max(theta(:,3)) - min(theta(:,3))));
        end
        
        if isfield(tl3, 'theta_dot')
            theta_dot = tl3.theta_dot;
            fprintf(fid, '   Peak Joint Velocities (deg/s):\n');
            fprintf(fid, '     Shoulder: %.1f\n', rad2deg(max(abs(theta_dot(:,1)))));
            fprintf(fid, '     Elbow:    %.1f\n', rad2deg(max(abs(theta_dot(:,2)))));
            fprintf(fid, '     Wrist:    %.1f\n', rad2deg(max(abs(theta_dot(:,3)))));
        end
    end
    
    %% 4. Dynamic Analysis
    fprintf(fid, '\n4. DYNAMIC ANALYSIS (JOINT TORQUES)\n');
    fprintf(fid, '-----------------------------------\n');
    
    % Two-link model torques
    if isfield(swing_data, 'two_link') && isfield(swing_data.two_link, 'tau')
        tau = swing_data.two_link.tau;
        fprintf(fid, '\n   Two-Link Model:\n');
        fprintf(fid, '   Peak Joint Torques (Nm):\n');
        fprintf(fid, '     Shoulder: %.2f (max), %.2f (min)\n', max(tau(:,1)), min(tau(:,1)));
        fprintf(fid, '     Elbow:    %.2f (max), %.2f (min)\n', max(tau(:,2)), min(tau(:,2)));
        fprintf(fid, '   RMS Joint Torques (Nm):\n');
        fprintf(fid, '     Shoulder: %.2f\n', rms(tau(:,1)));
        fprintf(fid, '     Elbow:    %.2f\n', rms(tau(:,2)));
    end
    
    % Three-link model torques
    if isfield(swing_data, 'three_link') && isfield(swing_data.three_link, 'tau')
        tau = swing_data.three_link.tau;
        fprintf(fid, '\n   Three-Link Model:\n');
        fprintf(fid, '   Peak Joint Torques (Nm):\n');
        fprintf(fid, '     Shoulder: %.2f (max), %.2f (min)\n', max(tau(:,1)), min(tau(:,1)));
        fprintf(fid, '     Elbow:    %.2f (max), %.2f (min)\n', max(tau(:,2)), min(tau(:,2)));
        fprintf(fid, '     Wrist:    %.2f (max), %.2f (min)\n', max(tau(:,3)), min(tau(:,3)));
        fprintf(fid, '   RMS Joint Torques (Nm):\n');
        fprintf(fid, '     Shoulder: %.2f\n', rms(tau(:,1)));
        fprintf(fid, '     Elbow:    %.2f\n', rms(tau(:,2)));
        fprintf(fid, '     Wrist:    %.2f\n', rms(tau(:,3)));
    end
    
    %% 5. Ball Trajectory Analysis
    if isfield(swing_data, 'ball')
        fprintf(fid, '\n5. BALL TRAJECTORY ANALYSIS\n');
        fprintf(fid, '---------------------------\n');
        
        ball = swing_data.ball;
        
        if isfield(ball, 'initial')
            init = ball.initial;
            if isfield(init, 'velocity')
                fprintf(fid, '   Initial ball velocity: %.2f m/s\n', norm(init.velocity));
            end
            if isfield(init, 'spin')
                fprintf(fid, '   Initial ball spin: %.1f rad/s\n', norm(init.spin));
            end
        end
        
        if isfield(ball, 'state') && isfield(ball, 'time')
            state = ball.state;
            fprintf(fid, '   Flight duration: %.3f s\n', ball.time(end));
            fprintf(fid, '   Final position: [%.2f, %.2f, %.2f] m\n', ...
                    state(end,1), state(end,2), state(end,3));
            fprintf(fid, '   Horizontal distance: %.2f m\n', ...
                    sqrt((state(end,1)-state(1,1))^2 + (state(end,3)-state(1,3))^2));
            fprintf(fid, '   Maximum height: %.2f m\n', max(state(:,2)));
        end
    end
    
    %% 6. Energy Analysis
    fprintf(fid, '\n6. ENERGY ANALYSIS\n');
    fprintf(fid, '------------------\n');
    
    if isfield(swing_data, 'two_link') && isfield(swing_data.two_link, 'tau') && ...
       isfield(swing_data.two_link, 'theta_dot') && isfield(swing_data, 'time')
        tau = swing_data.two_link.tau;
        theta_dot = swing_data.two_link.theta_dot;
        time = swing_data.time;
        dt = time(2) - time(1);
        
        % Power = torque * angular velocity
        power = sum(tau .* theta_dot, 2);
        
        % Total work = integral of power
        total_work = trapz(time, power);
        
        % Positive and negative work
        pos_work = trapz(time, max(power, 0));
        neg_work = trapz(time, min(power, 0));
        
        fprintf(fid, '   Two-Link Model:\n');
        fprintf(fid, '   Total mechanical work: %.2f J\n', total_work);
        fprintf(fid, '   Positive work (acceleration): %.2f J\n', pos_work);
        fprintf(fid, '   Negative work (deceleration): %.2f J\n', neg_work);
        fprintf(fid, '   Peak power output: %.2f W\n', max(power));
    end
    
end

%% Report Footer
fprintf(fid, '\n================================================================================\n');
fprintf(fid, '                           END OF REPORT\n');
fprintf(fid, '================================================================================\n');

%% Close File
if fid ~= 1
    fclose(fid);
    fprintf('Report saved to: %s\n', output_filename);
end

end

%% Helper function for RMS calculation
function y = rms(x)
    y = sqrt(mean(x.^2));
end
