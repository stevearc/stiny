angular.module('stiny')

.constant('CONST', angular.fromJson(angular.element(document.body).attr('constants')))

.config(['$httpProvider', ($httpProvider) ->
  $httpProvider.defaults.xsrfHeaderName = 'X-CSRF-Token'
  $httpProvider.defaults.xsrfCookieName = 'CSRF-Token'
])

.run(->
  FastClick.attach(document.body)
)

.directive('stFocus', ['$timeout', ($timeout) ->
  (scope, element, attrs) ->
    scope.$watch(attrs.stFocus,
      (newValue) ->
        if newValue
          $timeout(->
            element[0].focus()
            if not attrs.noScroll?
              window.scrollTo(0, element[0].offsetTop - 100)
          )
      , true)
])

# Intercept all HTTP errors. If they contain a nice code and message, log it to
# the console.
.config(['$httpProvider', ($httpProvider) ->
  $httpProvider.interceptors.push(['$q', '$injector', ($q, $injector) ->
    login = ['stAuth', (stAuth) ->
      stAuth.removeUser()
      stAuth.login()
    ]
    return {
      responseError: (response) ->
        if response.status == 401
          $injector.invoke(login)
        else if response.data.error? and response.data.msg?
          console.log("#{response.data.error}: #{response.data.msg}")
        $q.reject(response)
    }
  ])
])

.factory('stAuth', ['$http', '$route', '$location', '$injector',
($http, $route, $location, $injector) -> {
    _user: null
    _permissions: []
    getUser: -> @_user
    setUser: (@_user) ->
    setPermissions: (@_permissions) ->
    hasPermission: (perm) ->
      if 'admin' in @_permissions
        return true
      return perm in @_permissions
    removeUser: -> @_user = null
    # FIXME: Logout doesn't work right now
    logout: ->
      gapi.auth.signOut()
    serverLogout: ->
      $http.post('/api/logout').success((data, status, headers, config) =>
        @removeUser()
        $route.reload()
      )
    login: ->
      $location.url('/login')
  }
])

.directive('stPermShow', ['stAuth', (stAuth) ->
  restrict: 'A'
  replace: true
  link: (scope, element, attrs) ->
    perm = attrs.stPermShow
    scope.$watch(->
      stAuth.hasPermission(perm)
    (hasPerm) ->
      if hasPerm
        element.removeClass('hide')
      else
        element.addClass('hide')
    )
])

.run(['stAuth', 'CONST', (stAuth, CONST) ->
  if CONST.USER?
    stAuth.setUser(CONST.USER)
  if CONST.PERMISSIONS?
    stAuth.setPermissions(CONST.PERMISSIONS)
])
