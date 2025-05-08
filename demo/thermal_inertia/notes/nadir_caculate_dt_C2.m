% 传递函数系数，考虑震荡衰减
B = [0.3268, 0.08357, 0.003767, 9.953e-05];  % 分子系数
A = [1, 0.6486, 0.2147, 0.01986, 0.0002119]; % 分母系数

% 极点-留数分解
[R, P, ~] = residue(B, A);

% 展示更加精确的极点和留数
fprintf('极点 (Poles):\n');
for k = 1:length(P)
    fprintf('%20.12e %+20.12ei\n', real(P(k)), imag(P(k)));
end
fprintf('留数 (Residues):\n');
for k = 1:length(R)
    fprintf('%20.12e %+20.12ei\n', real(R(k)), imag(R(k)));
end

% 分离实极点和复极点
real_poles_idx = abs(imag(P)) < 1e-10; % 实极点
real_poles = P(real_poles_idx);
real_residues = R(real_poles_idx);
complex_poles = P(~real_poles_idx);
complex_residues = R(~real_poles_idx);

% 按衰减速度排序实极点
[~, sorted_idx] = sort(real_poles, 'ascend'); % 实部从小到大（衰减从慢到快）
slow_pole_idx = sorted_idx(1); % 缓慢衰减（实部最接近 0）
fast_pole_idx = sorted_idx(2); % 快速衰减（实部更负）

% 提取参数
% 快速衰减项（C0, T0）
P0 = real_poles(slow_pole_idx);
T0 = -1/real(P0);
C0 = real(real_residues(slow_pole_idx)/P0);

% 缓慢衰减项（C1, T1）
P1 = real_poles(fast_pole_idx);
T1 = -1/real(P1);
C1 = real(real_residues(fast_pole_idx)/P1);

% 振荡衰减项（C2, T2, omega2, theta）
P2 = complex_poles(1); % 取虚部为正的复极点
alpha = real(P2);
beta = imag(P2);
T2 = -1/alpha;
omega2 = beta;
R2 = complex_residues(1);
C2 = 2 * abs(R2/P2); % 因子 2 因为有两个共轭极点
theta = angle(R2/P2);

Pd = -0.04;  % 比例系数，匹配最低频率 -0.012 p.u.

% 打印参数（提高精度）
fprintf('\n计算得到的参数:\n');
fprintf('C0 (快速衰减) = %.6f, T0 = %.12f\n', C0, T0);
fprintf('C1 (缓慢衰减) = %.6f, T1 = %.12f\n', C1, T1);
fprintf('C2 (振荡衰减) = %.6f, T2 = %.12f, omega2 = %.12f, theta = %.12f\n', C2, T2, omega2, theta);

% 定义 y(t) 的导数函数（仅考虑 C2，从 t = 0 开始）
y_deriv = @(t) C2 * (-1/T2 * exp(-t/T2) .* cos(omega2*t + theta) - ...
                      omega2 * exp(-t/T2) .* sin(omega2*t + theta));

% 初始猜测值（基于 3.67 秒）
t_guess = 4.25;  % 从 0 秒开始的猜测时间

% 使用 fsolve 求解导数为零的点
options = optimset('Display', 'off', 'TolX', 1e-6);
t_min = fsolve(y_deriv, t_guess, options);

% 显示结果
fprintf('Lowest frequency time (oscillatory only): %.2f seconds\n', t_min);

% 可选：验证导数值（接近零）
deriv_value = y_deriv(t_min);
fprintf('Derivative at t = %.2f: %.6f (should be close to 0)\n', t_min, deriv_value);

% 计算完整的 y(t)（包含所有三项）以计算频率偏差
y_value = C0 * (exp(-t_min/T0) - 1) + C1 * (exp(-t_min/T1) - 1) + ...
          C2 * (exp(-t_min/T2) .* cos(omega2*t_min + theta) - cos(theta));
freq_dev = Pd * y_value * 60;  % 使用 Pd
fprintf('y(t) at t = %.2f: %.6f\n', t_min, y_value);
fprintf('Lowest frequency deviation (all terms): %.6f p.u.\n', 60+freq_dev);

% 定义仿真时间（从 0 秒开始）
t_values = 0:0.01:20;  % 调整为 0-20 秒，覆盖主要动态

% 计算完整的 y(t) 曲线（仅用于绘图，包含所有三项）
y_values = C0 * (exp(-t_values/T0) - 1) + C1 * (exp(-t_values/T1) - 1) + ...
           C2 * (exp(-t_values/T2) .* cos(omega2*t_values + theta) - cos(theta));
dy_values = C2 * (-1/T2 * exp(-t_values/T2) .* cos(omega2*t_values + theta) - ...
                  omega2 * exp(-t_values/T2) .* sin(omega2*t_values + theta));

% 计算频率偏差曲线
f_t = Pd * y_values * 60;

% 绘制时域响应曲线
figure;
subplot(2,1,1);
plot(t_values, f_t, 'r--', 'LineWidth', 1.5);
xlabel('时间 (s)');
ylabel('频率偏差 (p.u.)');
title(sprintf('阶跃响应时域输出 (仅振荡衰减求导)\nΔf(t) = %.6f[%.6f(e^{-t/%.2f}-1) + %.6f(e^{-t/%.2f}-1) + %.6f(e^{-t/%.2f}cos(%.4ft - %.4f)-cos(%.4f))] * 60', ...
    Pd, C0, T0, C1, T1, C2, T2, omega2, theta, theta));
grid on;
hold on;
plot(t_min, freq_dev, 'bo', 'MarkerSize', 10);  % 标记最低点
legend('时域响应', '最低频率点');

% 绘制 y'(t) 曲线以验证（仅振荡项）
subplot(2,1,2);
plot(t_values, dy_values, 'r-', t_min, deriv_value, 'ro');
grid on;
xlabel('时间 (s)');
ylabel("y'(t)");
title('导数曲线 (仅振荡衰减)');