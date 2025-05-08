%% === Load ANDES simulation data ===
load('andes_data.mat');  % Contains t and omega_s2

% === Calculate frequency deviation based on 60Hz reference ===
y1 = (omega_s2 - 60)/60;  % Output frequency deviation

% === Construct input signal (disturbance occurs at 1 second) ===
u = zeros(size(t));
u(t >= 1) = -0.04;  % Step decrease after 1 second

% === Interpolation (increase sampling precision) ===
Ts = mean(diff(t)) / 3;  % Sampling period after interpolation
t_uniform = (t(1):Ts:t(end))';

% Interpolation
y1_interp = interp1(t, y1, t_uniform, 'linear', 'extrap');
u_interp = interp1(t, u, t_uniform, 'previous', 'extrap');

%% === Use tfest for system identification ===
data_id = iddata(y1_interp, u_interp, Ts); % Create iddata object

sys_tf = tfest(data_id, 4, 3);
% 4th-order system, 3 zeros, simulation focus

%% === Simulate system output after identification ===
y_fit = lsim(sys_tf, u_interp, t_uniform);

% Calculate the steady-state value of y_fit
y_ss = y_fit(end);  % Take the last point of the simulation output as the steady-state value

%% === Plot comparison ===
figure;
plot(t, 60+y1*60, 'k', 'LineWidth', 1.5);hold on;

% plot(t_uniform, y1_interp, 'g--', 'LineWidth', 1.5);

plot(t_uniform,60+ y_fit*60, 'b-.', 'LineWidth', 1.5);

% yline(y_ss, 'r--', 'LineWidth', 1.2, 'Label', 'Steady-state Value', 'LabelHorizontalAlignment', 'left');

xlabel('Time (s)');
ylabel('Frequency Deviation (Hz)');
title('Transfer Function Identification from ANDES Simulation Output (Step at 1s)');
grid on;
legend('Original Simulation Output', 'Identified Model Output', 'Location', 'best');

% Calculate frequency (unit: Hz)
f_sim = 60 + y1 * 60;
f_fit = 60 + y_fit * 60;

% Save the four variables you need
save('sfr_result_80wind.mat', 't', 'f_sim', 't_uniform', 'f_fit');

%% === Print the identified discrete transfer function ===
disp('=== Identified Discrete Transfer Function ===');
sys_tf
