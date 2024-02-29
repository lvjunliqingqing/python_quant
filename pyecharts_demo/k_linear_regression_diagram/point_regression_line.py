import numpy as np


def point_regression_line(point, line_point1, line_point2):
    """收盘价点到收盘价的回归线的距离"""
    # 对于两点坐标为同一点时,返回点与点的距离
    if line_point1 == line_point2:
        point_array = np.array(point)
        point1_array = np.array(line_point1)
        return np.linalg.norm(point_array - point1_array)
    # 计算直线的三个参数
    A = line_point2[1] - line_point1[1]  # 横截距
    B = line_point1[0] - line_point2[0]  # 纵截距
    C = (line_point1[1] - line_point2[1]) * line_point1[0] + (line_point2[0] - line_point1[0]) * line_point1[1]
    # 根据点到直线的距离公式计算距离
    distance = np.abs(A * point[0] + B * point[1] + C) / (np.sqrt(A ** 2 + B ** 2))
    distance = round(distance / point[1], 6)
    # distance = round(distance, 4)
    if point[1] < line_point2[1]:
        return -distance
    return distance


if __name__ == '__main__':
    print(point_regression_line([5, 9], [0, 0], [5, 8]))
    """
    设所有的直线方程为二元一次方程:Ax+By+C=0
    把直线(0,0)和(5,8)两点代入公式得到:0A+0B+C=0 和 5A+8B+C=0
    由此得出直线方程为:8x-5y=0
    """