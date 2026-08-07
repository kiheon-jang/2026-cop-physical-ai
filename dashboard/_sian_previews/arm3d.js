/* ============================================================================
 * arm3d.js — CoP 히어로 3D 로봇팔 (SO-101 · hdel_iot_01)
 * 대시보드 sim3d 뷰어(template.html)의 **검증된** 체인 렌더를 그대로 재사용.
 * FK 각도를 추측하지 않는다: web3d_chain(실 MuJoCo export)의 바디 트랜스폼 +
 * 조인트 축/피벗으로 팔을 세우고, 실측 qpos6 를 hinge 에 그대로 적용한다.
 *   - 좌표: MuJoCo Z-up → three Y-up 은 root 만 -90°X 회전, 내부는 MuJoCo 그대로.
 *   - 바디 트리: body.pos/quat 로 Group 중첩, hinge 는 pivot/neg 쌍으로 자식 보정.
 *   - 관절: pivot.quaternion.setFromAxisAngle(axisV, q[qposadr]) — sign/offset 없음.
 * 전역 THREE(r152) + REAL_TRAJ(real_traj_full.json) + WEB3D_CHAIN(web3d_chain.json).
 * canvas#hero3d 렌더. 드래그=회전 / 휠=줌. led_frame 부터 LED 점등.
 * ==========================================================================*/
(function (global) {
  "use strict";

  /* MuJoCo quat(w,x,y,z) → THREE(x,y,z,w) — sim3d 와 동일 */
  function mjq(THREE, q) { return new THREE.Quaternion(q[1], q[2], q[3], q[0]); }

  /* b64 → Float32/Uint32 (sim3d b64ToF32/b64ToU32 그대로) */
  function b64ToF32(s) {
    var bin = atob(s), u8 = new Uint8Array(bin.length);
    for (var i = 0; i < bin.length; i++) u8[i] = bin.charCodeAt(i);
    return new Float32Array(u8.buffer);
  }
  function b64ToU32(s) {
    var bin = atob(s), u8 = new Uint8Array(bin.length);
    for (var i = 0; i < bin.length; i++) u8[i] = bin.charCodeAt(i);
    return new Uint32Array(u8.buffer);
  }

  /* ── 다크 톤 팔레트 (B_main_v2 :root) ── */
  var COL = {
    metal: 0x2a2f3a,   // 메탈 회색 바디
    jaw:   0xeef2f8,   // 흰 이동턱 (moving_jaw)
    pcb:   0x123a24,   // 어두운 초록 기판
    btn:   0x991a1a,   // 리셋버튼 빨강 (0.6 0.1 0.1)
    ledOff:0x244d33,   // LED 꺼짐
    ledOn: 0x22e06b,   // LED 발광 초록
  };

  /* ── 씬 구성: web3d_chain 으로 팔 빌드 (sim3dBuildScene 이식) ── */
  function buildHero(THREE, chain, RT, canvasId, interactive) {
    var canvas = document.getElementById(canvasId || "hero3d");
    if (!canvas) return null;
    var W = canvas.clientWidth || 460, H = canvas.clientHeight || 312;

    var renderer = new THREE.WebGLRenderer({ canvas: canvas, antialias: true, alpha: true });
    renderer.setPixelRatio(Math.min(global.devicePixelRatio || 1, 2));
    renderer.setSize(W, H, false);
    renderer.outputColorSpace = THREE.SRGBColorSpace;
    renderer.toneMapping = THREE.NoToneMapping;
    renderer.shadowMap.enabled = true;
    renderer.shadowMap.type = THREE.PCFSoftShadowMap;

    var scene = new THREE.Scene();  // 배경 투명 → #hero3d CSS 딥네이비 그라디언트 노출

    // 다크 톤 조명: 낮은 앰비언트 + 쿨 화이트 키 + 시안/민트 미묘한 림
    scene.add(new THREE.HemisphereLight(0x3a4a5f, 0x05070e, 0.5));
    var key = new THREE.DirectionalLight(0xd6e6ff, 1.15);
    key.position.set(0.55, 1.35, 0.85);
    key.castShadow = true;
    key.shadow.mapSize.set(2048, 2048);
    key.shadow.camera.near = 0.05; key.shadow.camera.far = 4;
    key.shadow.camera.left = -0.5; key.shadow.camera.right = 0.5;
    key.shadow.camera.top = 0.5; key.shadow.camera.bottom = -0.5;
    key.shadow.bias = -0.0005; key.shadow.normalBias = 0.02;
    scene.add(key);
    var rimC = new THREE.DirectionalLight(0x39c6f0, 0.5); rimC.position.set(-0.8, 0.45, -0.7); scene.add(rimC);
    var rimM = new THREE.DirectionalLight(0x2ee6a0, 0.32); rimM.position.set(-0.3, 0.3, 0.6); scene.add(rimM);

    // MuJoCo Z-up → three Y-up: root 만 -90° X. 내부 좌표는 MuJoCo 그대로.
    var root = new THREE.Group();
    root.rotation.x = -Math.PI / 2;
    scene.add(root);

    // 바닥 접촉 그림자(팔이 허공에 뜨지 않고 바닥에 선 느낌) — 투명 ShadowMaterial
    var ground = new THREE.Mesh(
      new THREE.PlaneGeometry(1.6, 1.6),
      new THREE.ShadowMaterial({ opacity: 0.42 }));
    ground.position.z = 0; ground.receiveShadow = true; root.add(ground);
    // 미묘한 다크 그리드(스케일 감) — three world Y-up
    var grid = new THREE.GridHelper(1.4, 28, 0x1c3a4a, 0x11202c);
    grid.position.y = 0.0005; scene.add(grid);

    // 메시 지오메트리 (chain.meshes → BufferGeometry) — sim3d 그대로
    var geoms = {};
    Object.keys(chain.meshes).forEach(function (name) {
      var m = chain.meshes[name];
      var g = new THREE.BufferGeometry();
      g.setAttribute("position", new THREE.BufferAttribute(b64ToF32(m.verts_b64), 3));
      g.setIndex(new THREE.BufferAttribute(b64ToU32(m.faces_b64), 1));
      g.computeVertexNormals();
      geoms[name] = g;
    });

    var cubeBody = chain.bodies.find(function (b) { return b.name === "cube"; });
    var cubeId = cubeBody ? cubeBody.id : -1;
    var jawBody = chain.bodies.find(function (b) { return b.name === "moving_jaw_so101_v1"; });
    var jawId = jawBody ? jawBody.id : -1;

    var metalMat = new THREE.MeshStandardMaterial({ color: COL.metal, metalness: 0.6, roughness: 0.42 });
    var jawMat   = new THREE.MeshStandardMaterial({ color: COL.jaw,   metalness: 0.28, roughness: 0.34 });

    // geom → mesh (sim3d geomMesh 구조, 단 톤다운: rgba 무시하고 다크 메탈/흰 턱)
    function geomMesh(ge) {
      if (ge.type === "plane") return null;           // 전용 바닥 사용
      if (ge.name === "table") return null;           // S1 = 바닥 씬, 받침대 숨김
      if (ge.body === cubeId) return null;            // 큐브 파지 대상 아님(리셋버튼 씬)
      var mat = (ge.body === jawId) ? jawMat : metalMat;
      var mesh = null;
      if (ge.type === "mesh" && geoms[ge.mesh]) mesh = new THREE.Mesh(geoms[ge.mesh], mat);
      else if (ge.type === "box") mesh = new THREE.Mesh(new THREE.BoxGeometry(ge.size[0] * 2, ge.size[1] * 2, ge.size[2] * 2), mat);
      else if (ge.type === "sphere") mesh = new THREE.Mesh(new THREE.SphereGeometry(ge.size[0], 20, 14), mat);
      else if (ge.type === "cylinder") mesh = new THREE.Mesh(new THREE.CylinderGeometry(ge.size[0], ge.size[0], ge.size[1] * 2, 20).rotateX(Math.PI / 2), mat);
      if (!mesh) return null;
      mesh.castShadow = true; mesh.receiveShadow = true;
      mesh.position.fromArray(ge.pos);
      mesh.quaternion.copy(mjq(THREE, ge.quat));
      return mesh;
    }

    // 바디 트리 + hinge 피벗 — sim3d 이식 그대로
    var bodyGroup = {}, inner = {};
    chain.bodies.forEach(function (b) {
      if (b.id === cubeId) return;                    // 큐브 바디 자체 스킵
      var g = new THREE.Group();
      g.position.fromArray(b.pos);
      g.quaternion.copy(mjq(THREE, b.quat));
      bodyGroup[b.id] = g; inner[b.id] = g;
    });
    var hinges = [];
    chain.joints.forEach(function (j) {
      if (j.type !== "hinge") return;
      if (!bodyGroup[j.body]) return;
      var pivot = new THREE.Group(); pivot.position.fromArray(j.pos);
      var neg = new THREE.Group(); neg.position.set(-j.pos[0], -j.pos[1], -j.pos[2]);
      pivot.add(neg);
      bodyGroup[j.body].add(pivot);
      inner[j.body] = neg;
      hinges.push({ qposadr: j.qposadr, pivot: pivot, axisV: new THREE.Vector3().fromArray(j.axis).normalize() });
    });
    chain.geoms.forEach(function (ge) {
      var m = geomMesh(ge); if (!m) return;
      if (inner[ge.body]) inner[ge.body].add(m);
    });
    chain.bodies.forEach(function (b) {
      if (b.id === cubeId) return;
      if (b.id === 0) { root.add(bodyGroup[0]); return; }
      if (inner[b.parent]) inner[b.parent].add(bodyGroup[b.id]);
    });

    // ── PCB 무대: 초록 보드 + 작은 빨간 리셋버튼 + LED (sim3d 트윈 그대로) ──
    var pcb = (RT && RT.pcb) || { x: 0.27, y: 0, yaw_deg: 0 };
    var pcbG = new THREE.Group();
    var board = new THREE.Mesh(new THREE.BoxGeometry(0.15, 0.15, 0.01),
      new THREE.MeshStandardMaterial({ color: COL.pcb, roughness: 0.7, metalness: 0.08 }));
    board.receiveShadow = true;
    var btn = new THREE.Mesh(new THREE.CylinderGeometry(0.004, 0.004, 0.006, 16).rotateX(Math.PI / 2),
      new THREE.MeshStandardMaterial({ color: COL.btn, emissive: 0x330808, roughness: 0.5 }));
    btn.position.set(0, 0, 0.008); btn.castShadow = true;
    var led = new THREE.Mesh(new THREE.BoxGeometry(0.008, 0.008, 0.004),
      new THREE.MeshStandardMaterial({ color: COL.ledOff, emissive: 0x000000, emissiveIntensity: 0 }));
    led.position.set(0.03, 0, 0.007);
    pcbG.add(board, btn, led);
    pcbG.position.set(pcb.x, pcb.y, 0.02);          // sim3d S1 배치 z=0.02
    pcbG.rotation.set(0, 0, (pcb.yaw_deg || 0) * Math.PI / 180);
    root.add(pcbG);

    // ── 간이 오빗(sim3d applyCam 그대로) — 팔+PCB+버튼 누름이 보이는 초기각 ──
    var target = new THREE.Vector3(0.15, 0.07, 0.0);
    var az = 0.82, el = 0.30, dist = 0.62;
    var camera = new THREE.PerspectiveCamera(42, W / H, 0.01, 20);
    function applyCam() {
      camera.position.set(
        target.x + dist * Math.cos(el) * Math.sin(az),
        target.y + dist * Math.sin(el),
        target.z + dist * Math.cos(el) * Math.cos(az));
      camera.lookAt(target);
    }
    applyCam();
    if (!interactive) {  // 궤도(드래그 회전/휠 확대) — interactive(Playground)는 마우스로 팔을 직접 조종하므로 끔
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
        e.preventDefault(); dist = Math.min(1.6, Math.max(0.28, dist * (1 + e.deltaY * 0.001))); applyCam();
      }, { passive: false });
    }

    return {
      renderer: renderer, scene: scene, camera: camera, canvas: canvas,
      hinges: hinges, led: led, applyCam: applyCam
    };
  }

  /* ── qpos6 → hinge (sim3d 그대로: setFromAxisAngle, sign/offset 없음) ── */
  function applyFrame(H, q) {
    H.hinges.forEach(function (h) {
      if (h.qposadr < 6) h.pivot.quaternion.setFromAxisAngle(h.axisV, q[h.qposadr]);
    });
  }
  function setLED(H, on) {
    var m = H.led.material;
    if (on) { m.color.setHex(COL.ledOn); m.emissive.setHex(COL.ledOn); m.emissiveIntensity = 1.1; }
    else    { m.color.setHex(COL.ledOff); m.emissive.setHex(0x000000); m.emissiveIntensity = 0; }
  }

  /* ── 라이브 D.web3d 에서 히어로 재생용 rollout 궤적 뽑기 (SPA 통합용) ──
     standalone(B_main_3d)은 window.REAL_TRAJ 주입 → 그걸 우선 사용.
     SPA(대시보드)는 window.DATA.web3d.policy_history 최신 측정의 성공 rollout 사용.
     policy frame = [q0..q5, cube...] (len 9/13) — applyFrame 이 q[qposadr<6]만 읽어 큐브열 무시. */
  function pickHeroTraj(web3d) {
    if (!web3d) return null;
    var ph = web3d.policy_history;
    var m = (ph && ph.length) ? ph[ph.length - 1]
          : (web3d.policy_rollouts ? { rollouts: [web3d.policy_rollouts], fps: web3d.policy_rollouts.fps } : null);
    if (!m || !m.rollouts || !m.rollouts.length) return null;
    var r = null;
    for (var i = 0; i < m.rollouts.length; i++) { if (m.rollouts[i] && m.rollouts[i].success) { r = m.rollouts[i]; break; } }
    if (!r) r = m.rollouts[0];
    if (!r || !r.frames || !r.frames.length) return null;
    return { frames: r.frames, fps: m.fps || r.fps || 29.4, n: r.frames.length,
             led_frame: (r.led_frame != null ? r.led_frame : null), pcb: r.pcb || null };
  }

  /* ── 부팅: 씬 + 재생 루프 + 콘솔 라벨 갱신 ──
     canvasId 별 인스턴스(멀티: Overview #hero3d + Playground #play3d). opts.frameId/ledId/playId 로 라벨 연결. */
  function mountArm3D(canvasId, opts) {
    opts = opts || {}; canvasId = canvasId || "hero3d";
    var flag = "__arm3d_" + canvasId;
    if (global[flag]) return true;              // 멱등: 캔버스별 1회 (재호출은 DATA 준비까지 재시도)
    var THREE = global.THREE;
    var DATA = global.DATA || {}, web3d = DATA.web3d || {};
    var CH = global.WEB3D_CHAIN || web3d.chain;
    var RT = global.REAL_TRAJ || pickHeroTraj(web3d);
    if (!THREE || !RT || !CH) return false;     // 서버모드=DATA(web3d) 아직이면 반환, 다음 호출 재시도
    var H = buildHero(THREE, CH, RT, canvasId, opts.interactive);
    if (!H) return false;
    global[flag] = true;

    var FR = RT.frames, FPS = RT.fps || 29.41, N = RT.n || FR.length, LEDF = RT.led_frame != null ? RT.led_frame : 1e9;
    var RM = global.matchMedia && global.matchMedia("(prefers-reduced-motion: reduce)").matches;

    var frameLbl = opts.frameId ? document.getElementById(opts.frameId) : null,
        ledLab = opts.ledId ? document.getElementById(opts.ledId) : null,
        playbtn = opts.playId ? document.getElementById(opts.playId) : null;
    var ledOn = false;
    function renderFrame(i) {
      applyFrame(H, FR[i]);
      var on = i >= LEDF;
      if (on !== ledOn) {
        ledOn = on; setLED(H, on);
        if (ledLab) { ledLab.textContent = on ? "LED ●" : "LED ○"; ledLab.style.color = on ? "var(--grn)" : ""; }
      }
      if (frameLbl) frameLbl.textContent = (i + 1) + "/" + N;
    }

    function draw() { H.renderer.render(H.scene, H.camera); }

    if (global.ResizeObserver) new ResizeObserver(function () {
      var w = H.canvas.clientWidth || 460, h = H.canvas.clientHeight || 312;
      H.renderer.setSize(w, h, false); H.camera.aspect = w / h; H.camera.updateProjectionMatrix();
      H.applyCam(); draw();
    }).observe(H.canvas);

    // ── Playground: 마우스로 팔 조종(스크럽) + 클릭으로 버튼 누름 (자동재생/궤도 없음) ──
    if (opts.interactive) {
      var maxF = (LEDF < N ? LEDF : N - 1);   // 프레임 0(홈)→maxF(버튼 눌림·LED 점등)
      function show(i) { renderFrame(i); H.applyCam(); draw(); }
      show(0);
      var counterEl = opts.counterId ? document.getElementById(opts.counterId) : null;
      var hintEl = opts.hintId ? document.getElementById(opts.hintId) : null, count = 0;
      H.canvas.addEventListener("pointermove", function (e) {
        var r = H.canvas.getBoundingClientRect();
        var t = Math.max(0, Math.min((e.clientX - r.left) / (r.width || 1), 1));
        show(Math.round(t * maxF));                     // 좌=쉬는 자세, 우로 갈수록 팔이 버튼으로 내려감
        if (hintEl && !hintEl.__hid) { hintEl.__hid = true; hintEl.style.opacity = "0"; }
      });
      H.canvas.addEventListener("pointerdown", function () {
        show(Math.min(N - 1, maxF + 3));                // 확실히 눌린 프레임(LED on)
        count++; if (counterEl) counterEl.textContent = count;
      });
      return true;
    }

    // prefers-reduced-motion: 버튼 누른(LED 점등) 정지 프레임
    if (RM) {
      renderFrame(LEDF < N ? LEDF : N - 1); H.applyCam(); draw();
      if (playbtn) playbtn.textContent = "▶ 재생";
      return true;
    }

    var playing = true, last = 0, acc = 0, frame = 0;
    renderFrame(0); H.applyCam(); draw();
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
      draw();
    }
    requestAnimationFrame(loop);
    return true;
  }

  /* Overview 히어로 (#hero3d) 래퍼 — 콘솔 라벨(framelbl/ledlab/playbtn) 연결 */
  function initHero3D() {
    return mountArm3D("hero3d", { frameId: "framelbl", ledId: "ledlab", playId: "playbtn" });
  }

  if (typeof module !== "undefined" && module.exports) {
    module.exports = { buildHero: buildHero, applyFrame: applyFrame, setLED: setLED, mountArm3D: mountArm3D };
  } else if (typeof document !== "undefined") {
    global.initHero3D = initHero3D;   // SPA 통합: DATA(web3d) 준비 후 renderBmcHome 이 재호출
    global.mountArm3D = mountArm3D;    // Playground(#play3d) 등 추가 인스턴스용
    if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", initHero3D);
    else initHero3D();
  }
})(typeof window !== "undefined" ? window : globalThis);
