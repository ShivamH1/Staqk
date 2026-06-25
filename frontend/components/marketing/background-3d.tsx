'use client'

import { useEffect, useRef } from 'react'
import * as THREE from 'three'

interface Background3DProps {
  className?: string
}

/**
 * Rotating wireframe-city WebGL backdrop for the marketing canvas.
 * Cycles through tinted dark scene colors and parallaxes to the cursor on XL
 * viewports; on smaller screens it auto-rotates. WebGL only runs in the effect,
 * so this is a client component (browser-only APIs).
 */
export default function Background3D({ className = '' }: Background3DProps) {
  const containerRef = useRef<HTMLDivElement>(null)
  const rendererRef = useRef<THREE.WebGLRenderer | null>(null)
  const animationFrameRef = useRef<number>(0)

  useEffect(() => {
    const container = containerRef.current
    if (!container) return

    const isXL = () => window.innerWidth >= 1280

    const renderer = new THREE.WebGLRenderer({ antialias: true })
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2))
    renderer.setSize(window.innerWidth, window.innerHeight)

    if (window.innerWidth > 800) {
      renderer.shadowMap.enabled = true
      renderer.shadowMap.type = THREE.PCFSoftShadowMap
    }

    container.appendChild(renderer.domElement)
    rendererRef.current = renderer

    const camera = new THREE.PerspectiveCamera(20, window.innerWidth / window.innerHeight, 1, 500)
    camera.position.set(0, 2, 14)

    const scene = new THREE.Scene()
    const city = new THREE.Object3D()
    const smoke = new THREE.Object3D()
    const town = new THREE.Object3D()

    const uSpeed = 0.001
    let createCarPos = true

    const darkColors = [0x232454, 0x442245, 0x215359, 0x522531, 0x22592d, 0x595423]

    let colorIndex = 0
    let colorTransitionTime = 0
    const colorTransitionDuration = 6000

    scene.background = new THREE.Color(darkColors[0])
    scene.fog = new THREE.Fog(darkColors[0], 10, 16)

    const mathRandom = (n = 8) => -Math.random() * n + Math.random() * n

    function init() {
      const segments = 2

      for (let i = 0; i < 100; i++) {
        const geo = new THREE.BoxGeometry(1, 1, 1, segments, segments, segments)
        const mat = new THREE.MeshStandardMaterial({
          color: 0x000000,
          emissive: 0x000000,
          emissiveIntensity: 0,
        })
        const wire = new THREE.MeshLambertMaterial({
          color: 0xffffff,
          wireframe: true,
          transparent: true,
          opacity: 0.02,
          emissive: 0x000000,
          emissiveIntensity: 0,
        })

        const cube = new THREE.Mesh(geo, mat)
        const wireMesh = new THREE.Mesh(geo, wire)
        const floor = new THREE.Mesh(geo, mat)

        cube.add(wireMesh)
        cube.castShadow = cube.receiveShadow = true

        cube.scale.y = 0.1 + Math.abs(mathRandom(8))
        cube.scale.x = cube.scale.z = 0.9 + mathRandom(0.1)

        cube.position.set(Math.round(mathRandom()), 0, Math.round(mathRandom()))

        floor.scale.y = 0.05
        floor.position.set(cube.position.x, 0, cube.position.z)

        town.add(floor)
        town.add(cube)
      }

      const pGeo = new THREE.CircleGeometry(0.01, 3)
      const pMat = new THREE.MeshToonMaterial({
        color: 0xffffff,
        emissive: 0xffffaa,
        emissiveIntensity: 0.3,
      })

      for (let i = 0; i < 300; i++) {
        const p = new THREE.Mesh(pGeo, pMat)
        p.position.set(mathRandom(5), mathRandom(5), mathRandom(5))
        smoke.add(p)
      }

      const ground = new THREE.Mesh(
        new THREE.PlaneGeometry(60, 60),
        new THREE.MeshPhongMaterial({ color: 0x000000, transparent: true, opacity: 0.9 }),
      )
      ground.rotation.x = -Math.PI / 2
      ground.position.y = -0.001
      ground.receiveShadow = true

      city.add(ground)
    }

    const ambient = new THREE.AmbientLight(0xffffff, 2.5)
    const front = new THREE.SpotLight(0xffffff, 20)
    const back = new THREE.PointLight(0xffffff, 0.5)

    front.position.set(5, 5, 5)
    front.castShadow = true
    back.position.set(0, 6, 0)

    smoke.position.y = 2

    scene.add(ambient, back)
    city.add(front, smoke, town)
    scene.add(city)

    city.add(new THREE.GridHelper(60, 120, 0xff0000, 0x000000))

    const createCars = (scale = 0.1, pos = 20) => {
      const car = new THREE.Mesh(
        new THREE.BoxGeometry(1, scale / 40, scale / 40),
        new THREE.MeshToonMaterial({ color: 0x333333, emissive: 0x000000, emissiveIntensity: 0 }),
      )

      if (createCarPos) {
        createCarPos = false
        car.position.set(-pos, Math.abs(mathRandom(5)), mathRandom(3))
      } else {
        createCarPos = true
        car.position.set(mathRandom(3), Math.abs(mathRandom(5)), -pos)
        car.rotation.y = Math.PI / 2
      }

      city.add(car)
    }

    for (let i = 0; i < 60; i++) createCars()

    const mouse = { x: 0, y: 0 }

    function onMouseMove(e: MouseEvent) {
      if (!isXL()) return
      mouse.x = (e.clientX / window.innerWidth) * 2 - 1
      mouse.y = -(e.clientY / window.innerHeight) * 2 + 1
    }

    function onResize() {
      camera.aspect = window.innerWidth / window.innerHeight
      camera.updateProjectionMatrix()
      renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2))
      renderer.setSize(window.innerWidth, window.innerHeight)
    }

    function animate() {
      animationFrameRef.current = requestAnimationFrame(animate)

      colorTransitionTime += 16

      if (colorTransitionTime >= colorTransitionDuration) {
        colorTransitionTime = 0
        colorIndex = (colorIndex + 1) % darkColors.length
      }

      const currentColor = darkColors[colorIndex]
      const nextColor = darkColors[(colorIndex + 1) % darkColors.length]
      const progress = colorTransitionTime / colorTransitionDuration

      const r1 = (currentColor >> 16) & 0xff
      const g1 = (currentColor >> 8) & 0xff
      const b1 = currentColor & 0xff

      const r2 = (nextColor >> 16) & 0xff
      const g2 = (nextColor >> 8) & 0xff
      const b2 = nextColor & 0xff

      const r = Math.round(r1 + (r2 - r1) * progress)
      const g = Math.round(g1 + (g2 - g1) * progress)
      const b = Math.round(b1 + (b2 - b1) * progress)

      const interpolatedColor = (r << 16) | (g << 8) | b

      ;(scene.background as THREE.Color)?.setHex(interpolatedColor)
      scene.fog?.color?.setHex(interpolatedColor)

      if (isXL()) {
        city.rotation.y -= (mouse.x * 8 - camera.rotation.y) * uSpeed
        city.rotation.x -= (-(mouse.y * 2) - camera.rotation.x) * uSpeed
      } else {
        city.rotation.y += 0.001
      }

      city.rotation.x = Math.max(-0.05, Math.min(1, city.rotation.x))

      smoke.rotation.y += 0.01
      smoke.rotation.x += 0.01

      camera.lookAt(city.position)
      renderer.render(scene, camera)
    }

    init()
    animate()

    window.addEventListener('resize', onResize)
    window.addEventListener('mousemove', onMouseMove)

    return () => {
      window.removeEventListener('resize', onResize)
      window.removeEventListener('mousemove', onMouseMove)

      cancelAnimationFrame(animationFrameRef.current)

      if (rendererRef.current && container) {
        container.removeChild(rendererRef.current.domElement)
        rendererRef.current.dispose()
      }

      scene.traverse((obj) => {
        if (obj instanceof THREE.Mesh) {
          obj.geometry.dispose()
          if (Array.isArray(obj.material)) {
            obj.material.forEach((m) => {
              m.dispose()
            })
          } else {
            obj.material.dispose()
          }
        }
      })
    }
  }, [])

  return <div ref={containerRef} className={`fixed inset-0 ${className}`} />
}
