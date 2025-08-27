import cv2
import numpy as np
import pygetwindow as gw
import pyautogui

template = r'F:\collect\pp_collect\build\pp_work_collect\data\pp_work.png'


def create_feature_detector():
    if hasattr(cv2, 'ORB_create'):
        print("[INFO] 使用 ORB 特征匹配")
        return cv2.ORB_create()
    elif hasattr(cv2, 'SIFT_create'):
        print("[INFO] 使用 SIFT 特征匹配")
        return cv2.SIFT_create()
    else:
        return None  # 没有特征匹配时用模板匹配

def screenshot_window(window_title):
    all_windows = gw.getWindowsWithTitle(window_title)
    win_list = [w for w in all_windows if getattr(w, 'isVisible', getattr(w, 'visible', False))]
    if not win_list:
        raise RuntimeError(f"未找到可见窗口: {window_title}")
    win = win_list[0]
    left, top, width, height = win.left, win.top, win.width, win.height
    print(f"[INFO] 找到窗口 '{window_title}' 位置: {left},{top},{width}x{height}")
    screenshot = pyautogui.screenshot(region=(left, top, width, height))
    img_path = "window_capture.png"
    screenshot.save(img_path)
    return img_path

def orb_sift_match(img, template, min_match_count=8):
    detector = create_feature_detector()
    if detector is None:
        print("[WARN] 无特征检测器，跳过特征匹配")
        return None

    kp1, des1 = detector.detectAndCompute(template, None)
    kp2, des2 = detector.detectAndCompute(img, None)
    if des1 is None or des2 is None:
        return None

    if detector.__class__.__name__.startswith("ORB"):
        bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=False)
    else:
        bf = cv2.BFMatcher()

    matches = bf.knnMatch(des1, des2, k=2)

    good = []
    for m, n in matches:
        if m.distance < 0.75 * n.distance:
            good.append(m)

    if len(good) >= min_match_count:
        src_pts = np.float32([kp1[m.queryIdx].pt for m in good]).reshape(-1, 1, 2)
        dst_pts = np.float32([kp2[m.trainIdx].pt for m in good]).reshape(-1, 1, 2)
        M, _ = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC, 5.0)
        h, w = template.shape
        pts = np.float32([[0, 0], [0, h], [w, h], [w, 0]]).reshape(-1, 1, 2)
        dst = cv2.perspectiveTransform(pts, M)
        return np.int32(dst)
    return None

def multi_scale_template_match(img, template, scale_range=(0.5, 1.5), step=0.1, threshold=0.8):
    h, w = template.shape
    best_val = -1
    best_loc = None
    best_scale = 1.0
    for scale in np.arange(scale_range[0], scale_range[1], step):
        resized = cv2.resize(template, (int(w * scale), int(h * scale)))
        if resized.shape[0] > img.shape[0] or resized.shape[1] > img.shape[1]:
            continue
        res = cv2.matchTemplate(img, resized, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
        if max_val > best_val:
            best_val = max_val
            best_loc = max_loc
            best_scale = scale
    if best_val >= threshold:
        print(f"[INFO] 模板匹配成功，相似度={best_val:.3f}，缩放={best_scale:.2f}")
        th, tw = int(h * best_scale), int(w * best_scale)
        top_left = best_loc
        bottom_right = (top_left[0] + tw, top_left[1] + th)
        return np.array([
            [top_left],
            [(top_left[0], bottom_right[1])],
            [bottom_right],
            [(bottom_right[0], top_left[1])]
        ], dtype=np.int32)
    else:
        print("[WARN] 模板匹配失败")
        return None

def match_image(full_img_path, template_path):
    img = cv2.imread(full_img_path, cv2.IMREAD_GRAYSCALE)
    template = cv2.imread(template_path, cv2.IMREAD_GRAYSCALE)
    if img is None or template is None:
        raise FileNotFoundError("图片路径错误")

    print("[INFO] 尝试 ORB/SIFT 特征匹配...")
    region = orb_sift_match(img, template)
    if region is None:
        print("[INFO] 特征匹配失败，尝试多尺度模板匹配...")
        region = multi_scale_template_match(img, template)

    if region is not None:
        img_out = cv2.polylines(img.copy(), [region], True, 255, 3, cv2.LINE_AA)
        cv2.imshow("Matched Result", img_out)
        cv2.waitKey(0)
        cv2.destroyAllWindows()
        return region
    else:
        print("[ERROR] 未匹配到目标")
        return None

if __name__ == "__main__":
    window_title = 'PP WORK'
    template_path = r'F:\collect\pp_collect\build\pp_work_collect\data\pp_work.png'
    full_img_path = screenshot_window(window_title)
    region = match_image(full_img_path, template_path)
    if region is not None:
        print("[RESULT] 匹配区域坐标:", region)


