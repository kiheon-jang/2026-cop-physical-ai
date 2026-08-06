/* ============================================================================
 * arm3d.js — CoP 히어로 3D 로봇팔 (SO-101 · hdel_iot_01)
 * 절차적(primitive) SO-101을 실측 rollout(qpos6)로 FK 구동.
 * 전역 THREE(r152 UMD) + 전역 REAL_TRAJ(real_traj_full.json) 사용.
 * canvas#hero3d 에 렌더. 드래그=궤도회전 / 휠=줌. led_frame부터 LED 점등.
 *
 * 브라우저: </body> 직전 주입 → 자동 시작(IIFE, DOMContentLoaded 안전).
 * node    : module.exports 로 buildArm/applyFK/setLED 노출(헤드리스 스모크).
 * ==========================================================================*/
(function (global) {
  "use strict";

  /* ── 링크 실측 비율(m) ── */
  var L_UP = 0.113, L_LO = 0.135, L_WR = 0.061;

  /* ── FK 캘리브레이션 노브 ──────────────────────────────────────────────
   * rotation = sign*qpos + offset(rad). 직접매핑(1:1). 브라우저에서 미세조정.
   * sign 은 서보 장착 방향, offset 은 링크를 +X(로컬)로 그린 것에 대한 중립 보정.
   * ponytail: 실기 URDF 없이 잡은 근사값 — 렌더 후 눈으로 nudge 하는 캘리브레이션 지점. */
  var CAL = {
    pan:   { s:  1, o: 0 },     // shoulder_pan  → Y(수직축) 요
    lift:  { s: -1, o: 0 },     // shoulder_lift → Z 피치
    elbow: { s:  1, o: 0 },     // elbow_flex    → Z 피치
    wf:    { s:  1, o: 0 },     // wrist_flex    → Z 피치
    roll:  { s:  1, o: 0 },     // wrist_roll    → X 롤
    jawGain: 3.2                // gripper qpos(≈0 닫힘) → 위턱 개구
  };

  /* ── 다크 B톤 팔레트(B_main_v2 :root 기준) ── */
  var COL = {
    metal:   0x22262f,  // 서보/링크 다크 메탈 (#1a1d24~#2a2f3a)
    metal2:  0x2a2f3a,
    bolt:    0x8a94a6,
    jaw:     0xeef2f8,  // 이동 위턱 밝은 흰/실버
    hook:    0x14171d,  // 고정 아래턱 검은 갈고리
    pcb:     0x0c3d2c,  // 어두운 초록 기판
    pcbLine: 0x1f7a58,
    btn:     0xff5d5d,  // 리셋버튼 빨강
    ledOff:  0x244d33,  // LED 꺼짐
    ledOn:   0x22e06b   // LED 발광 초록
  };

  function mkMetal(THREE, c)   { return new THREE.MeshStandardMaterial({ color: c || COL.metal, metalness: 0.55, roughness: 0.42 }); }
  function box(THREE, w, h, d, mat) { return new THREE.Mesh(new THREE.BoxGeometry(w, h, d), mat); }

  /* STS3215 서보 = 모서리 둥근(근사) 검은 박스 + 원형 혼 + 볼트 점 */
  function servo(THREE, w, h, d) {
    var g = new THREE.Group();
    g.add(box(THREE, w, h, d, mkMetal(THREE, COL.metal)));
    var horn = new THREE.Mesh(new THREE.CylinderGeometry(Math.min(w, h) * 0.28, Math.min(w, h) * 0.28, d * 1.04, 16), mkMetal(THREE, 0x12151b));
    horn.rotation.x = Math.PI / 2; g.add(horn);                       // 출력축 = Z
    var br = Math.min(w, h, d) * 0.05, bg = new THREE.SphereGeometry(br, 8, 6), bm = mkMetal(THREE, COL.bolt);
    [[-w * 0.34, h * 0.34], [w * 0.34, h * 0.34], [-w * 0.34, -h * 0.34], [w * 0.34, -h * 0.34]].forEach(function (p) {
      var b = new THREE.Mesh(bg, bm); b.position.set(p[0], p[1], d * 0.51); g.add(b);
    });
    return g;
  }

  /* ── 팔 씬그래프 구성: 중첩 Group(관절축별 회전) ──────────────────────── */
  function buildArm(THREE, RT) {
    RT = RT || (global.REAL_TRAJ || { pcb: { x: 0.27, y: 0, yaw_deg: 0 } });
    var armRoot = new THREE.Group();

    /* 베이스: 검은 3D프린트 받침 + 회전 서보 디스크 */
    var base = box(THREE, 0.10, 0.05, 0.075, mkMetal(THREE, 0x1a1e26)); base.position.y = 0.025;
    base.receiveShadow = true; armRoot.add(base);
    var topPlate = box(THREE, 0.10, 0.006, 0.075, mkMetal(THREE, COL.metal2)); topPlate.position.y = 0.05; armRoot.add(topPlate);
    var disc = new THREE.Mesh(new THREE.CylinderGeometry(0.032, 0.036, 0.02, 24), mkMetal(THREE, 0x12151b));
    disc.position.y = 0.062; armRoot.add(disc);

    /* panG: 수직축(Y) 요 회전 (shoulder_pan) */
    var panG = new THREE.Group(); panG.position.set(0, 0.072, 0); armRoot.add(panG);
    var shServo = servo(THREE, 0.048, 0.05, 0.05); shServo.position.set(0, 0.006, 0); panG.add(shServo);

    /* liftG: 피치(Z) 회전 (shoulder_lift) — upper_arm 두 평행 바 */
    var liftG = new THREE.Group(); liftG.position.set(0, 0.02, 0); panG.add(liftG);
    var upA = mkMetal(THREE, COL.metal2), x0 = 0.028;
    var barA = box(THREE, L_UP, 0.014, 0.012, upA); barA.position.set(x0 + L_UP / 2, 0, 0.014); liftG.add(barA);
    var barB = box(THREE, L_UP, 0.014, 0.012, upA); barB.position.set(x0 + L_UP / 2, 0, -0.014); liftG.add(barB);

    /* elbowG: 피치(Z) (elbow_flex) — lower_arm 단일 바 */
    var elbowG = new THREE.Group(); elbowG.position.set(x0 + L_UP, 0, 0); liftG.add(elbowG);
    var elServo = servo(THREE, 0.042, 0.044, 0.05); elbowG.add(elServo);
    var x1 = 0.024, lowerBar = box(THREE, L_LO, 0.03, 0.024, mkMetal(THREE, COL.metal)); lowerBar.position.set(x1 + L_LO / 2, 0, 0); elbowG.add(lowerBar);

    /* wflexG: 피치(Z) (wrist_flex) — wrist 링크 */
    var wflexG = new THREE.Group(); wflexG.position.set(x1 + L_LO, 0, 0); elbowG.add(wflexG);
    var wrServo = servo(THREE, 0.04, 0.04, 0.044); wflexG.add(wrServo);
    var x2 = 0.022, wristLink = box(THREE, L_WR, 0.026, 0.022, mkMetal(THREE, COL.metal2)); wristLink.position.set(x2 + L_WR / 2, 0, 0); wflexG.add(wristLink);

    /* rollG: 팔 축(X) 롤 (wrist_roll) → 그리퍼 */
    var rollG = new THREE.Group(); rollG.position.set(x2 + L_WR, 0, 0); wflexG.add(rollG);
    var collar = new THREE.Mesh(new THREE.CylinderGeometry(0.016, 0.016, 0.024, 18), mkMetal(THREE, COL.metal));
    collar.rotation.z = Math.PI / 2; collar.position.x = 0.012; rollG.add(collar);
    var gbase = box(THREE, 0.024, 0.03, 0.03, mkMetal(THREE, COL.metal2)); gbase.position.x = 0.03; rollG.add(gbase);

    /* 고정 아래턱: 검은 갈고리(뾰족) — 정지 */
    var hookMat = mkMetal(THREE, COL.hook);
    var jbase = box(THREE, 0.05, 0.012, 0.02, hookMat); jbase.position.set(0.065, -0.012, 0); rollG.add(jbase);
    var jtip = box(THREE, 0.03, 0.01, 0.016, hookMat); jtip.position.set(0.093, -0.02, 0); jtip.rotation.z = -0.5; rollG.add(jtip);

    /* 이동 위턱: 흰색(경첩) — jawG 만 gripper qpos로 여닫음 */
    var jawG = new THREE.Group(); jawG.position.set(0.05, 0.006, 0); rollG.add(jawG);
    var jawTop = box(THREE, 0.044, 0.011, 0.02, new THREE.MeshStandardMaterial({ color: COL.jaw, metalness: 0.3, roughness: 0.35 }));
    jawTop.position.set(0.022, 0, 0); jawG.add(jawTop);

    /* ── PCB 무대: 어두운 초록 기판 + 리셋버튼(빨강) + LED ── */
    var pcb = RT.pcb || { x: 0.27, y: 0, yaw_deg: 0 };
    var pcbG = new THREE.Group();
    pcbG.position.set(pcb.x, 0.004, pcb.y);
    pcbG.rotation.y = -(pcb.yaw_deg || 0) * Math.PI / 180;
    var board = box(THREE, 0.15, 0.008, 0.14, new THREE.MeshStandardMaterial({ color: COL.pcb, roughness: 0.7, metalness: 0.1 }));
    board.receiveShadow = true; pcbG.add(board);
    var btn = new THREE.Mesh(new THREE.CylinderGeometry(0.014, 0.014, 0.012, 20),
      new THREE.MeshStandardMaterial({ color: COL.btn, emissive: 0x5a1414, roughness: 0.5 }));
    btn.position.set(0, 0.01, 0); pcbG.add(btn);
    var led = new THREE.Mesh(new THREE.CylinderGeometry(0.01, 0.01, 0.008, 16),
      new THREE.MeshStandardMaterial({ color: COL.ledOff, emissive: 0x000000, emissiveIntensity: 0 }));
    led.position.set(0.05, 0.008, 0); pcbG.add(led);

    return {
      armRoot: armRoot, pcbG: pcbG,
      joints: { panG: panG, liftG: liftG, elbowG: elbowG, wflexG: wflexG, rollG: rollG, jawG: jawG },
      led: led, btn: btn
    };
  }

  /* ── 순수 FK: qpos6 → 각 Group 회전(6개 값 전부 사용) ── */
  function applyFK(J, q) {
    J.panG.rotation.y   = CAL.pan.s   * q[0] + CAL.pan.o;
    J.liftG.rotation.z  = CAL.lift.s  * q[1] + CAL.lift.o;
    J.elbowG.rotation.z = CAL.elbow.s * q[2] + CAL.elbow.o;
    J.wflexG.rotation.z = CAL.wf.s    * q[3] + CAL.wf.o;
    J.rollG.rotation.x  = CAL.roll.s  * q[4] + CAL.roll.o;
    J.jawG.rotation.z   = -Math.max(0, q[5]) * CAL.jawGain;   // 위턱만 개구
  }

  /* ── LED 점등 토글(led_frame 이후) ── */
  function setLED(A, on) {
    var m = A.led.material;
    if (on) { m.color.setHex(COL.ledOn); m.emissive.setHex(COL.ledOn); m.emissiveIntensity = 1.15; }
    else    { m.color.setHex(COL.ledOff); m.emissive.setHex(0x000000); m.emissiveIntensity = 0; }
  }

  /* ── 브라우저 부팅: 씬 + 오빗 + 재생루프 ─────────────────────────────── */
  function initHero3D() {
    var THREE = global.THREE, RT = global.REAL_TRAJ;
    var canvas = document.getElementById("hero3d");
    if (!THREE || !RT || !canvas) return;

    var RM = global.matchMedia && global.matchMedia("(prefers-reduced-motion: reduce)").matches;
    var FR = RT.frames, FPS = RT.fps || 29.41, N = RT.n || FR.length, LEDF = RT.led_frame || 0;

    var W = canvas.clientWidth || 460, H = canvas.clientHeight || 312;
    var renderer = new THREE.WebGLRenderer({ canvas: canvas, antialias: true, alpha: true });
    renderer.setPixelRatio(Math.min(global.devicePixelRatio || 1, 2));
    renderer.setSize(W, H, false);
    renderer.outputColorSpace = THREE.SRGBColorSpace;

    var scene = new THREE.Scene();               // 배경 투명 → 콘솔 딥네이비가 비침
    scene.add(new THREE.HemisphereLight(0x2a3a4a, 0x05070e, 0.55));
    var key = new THREE.DirectionalLight(0xbfe9ff, 0.95); key.position.set(0.6, 1.2, 0.8); scene.add(key);
    var rimC = new THREE.DirectionalLight(0x39c6f0, 0.6); rimC.position.set(-0.7, 0.5, -0.9); scene.add(rimC);   // 시안 림
    var rimM = new THREE.DirectionalLight(0x2ee6a0, 0.4); rimM.position.set(-0.4, 0.2, 0.6); scene.add(rimM);    // 민트 림

    var grid = new THREE.GridHelper(1.4, 28, 0x1c3a4a, 0x12202c); grid.position.y = 0.0005; scene.add(grid);

    var A = buildArm(THREE, RT);
    scene.add(A.armRoot); scene.add(A.pcbG);

    var camera = new THREE.PerspectiveCamera(42, W / H, 0.01, 20);
    /* 오빗(직접 구현): az=방위, el=고도, dist=줌. 카메라 초기 각도 = 팔+PCB 보기좋게 */
    var target = new THREE.Vector3(0.14, 0.1, 0);
    var az = 0.92, el = 0.34, dist = 0.6;
    function applyCam() {
      camera.position.set(
        target.x + dist * Math.cos(el) * Math.sin(az),
        target.y + dist * Math.sin(el),
        target.z + dist * Math.cos(el) * Math.cos(az));
      camera.lookAt(target);
      renderer.render(scene, camera);
    }
    var drag = null;
    canvas.addEventListener("pointerdown", function (e) { drag = { x: e.clientX, y: e.clientY }; canvas.setPointerCapture(e.pointerId); });
    canvas.addEventListener("pointermove", function (e) {
      if (!drag) return;
      az -= (e.clientX - drag.x) * 0.008;
      el = Math.min(1.45, Math.max(-0.15, el + (e.clientY - drag.y) * 0.006));
      drag = { x: e.clientX, y: e.clientY }; applyCam();
    });
    canvas.addEventListener("pointerup", function () { drag = null; });
    canvas.addEventListener("pointercancel", function () { drag = null; });
    canvas.addEventListener("wheel", function (e) {
      e.preventDefault(); dist = Math.min(1.6, Math.max(0.25, dist * (1 + e.deltaY * 0.001))); applyCam();
    }, { passive: false });

    /* 상태 라벨(콘솔 foot) */
    var frameLbl = document.getElementById("framelbl"), ledLab = document.getElementById("ledlab"), playbtn = document.getElementById("playbtn");
    var ledOn = false;
    function renderFrame(i) {
      applyFK(A.joints, FR[i]);
      var on = i >= LEDF;
      if (on !== ledOn) { ledOn = on; setLED(A, on); A.btn.position.y = on ? 0.007 : 0.01; if (ledLab) { ledLab.textContent = on ? "LED ●" : "LED ○"; ledLab.style.color = on ? "var(--grn)" : ""; } }
      if (frameLbl) frameLbl.textContent = (i + 1) + "/" + N;
    }

    function resize() {
      var w = canvas.clientWidth || 460, h = canvas.clientHeight || 312;
      renderer.setSize(w, h, false); camera.aspect = w / h; camera.updateProjectionMatrix(); applyCam();
    }
    if (global.ResizeObserver) new ResizeObserver(resize).observe(canvas);

    /* prefers-reduced-motion: 누른 자세 + LED 켜짐 정적 표시, 루프 없음 */
    if (RM) {
      renderFrame(LEDF); applyCam();
      if (playbtn) { playbtn.textContent = "▶ 재생"; }
      return;
    }

    /* 자동재생: fps로 루프. 재생/정지 토글 */
    var playing = true, last = 0, acc = 0, frame = 0;
    renderFrame(0); applyCam();
    if (playbtn) playbtn.addEventListener("click", function () {
      playing = !playing; playbtn.textContent = playing ? "❚❚ 일시정지" : "▶ 재생";
    });
    function loop(t) {
      requestAnimationFrame(loop);
      var dt = Math.min(0.1, (t - last) / 1000 || 0); last = t;
      if (playing) {
        acc += dt * FPS;
        while (acc >= 1) { acc -= 1; frame = (frame + 1) % N; }
        renderFrame(frame);
      }
      renderer.render(scene, camera);
    }
    requestAnimationFrame(loop);
  }

  /* ── 진입점 ── */
  if (typeof module !== "undefined" && module.exports) {
    module.exports = { buildArm: buildArm, applyFK: applyFK, setLED: setLED, CAL: CAL };
  } else if (typeof document !== "undefined") {
    if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", initHero3D);
    else initHero3D();
  }
})(typeof window !== "undefined" ? window : globalThis);
