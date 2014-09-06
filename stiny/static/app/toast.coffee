angular.module('stiny')

.factory('stToast', ['$timeout', ($timeout) ->
  {
    toasts: []
    toast: (text, duration=3000) ->
      toast = {
        text: text
      }
      # prevent duplicate toasts
      for t in @toasts
        if angular.equals(toast, t)
          return
      @toasts.push(toast)
      $timeout(=>
        @toasts.splice(@toasts.indexOf(toast), 1)
      , duration)

  }
])

.directive('stToaster', ['$document', 'stToast', 'CONST',
($document, stToast, CONST) ->
  restrict: 'A'
  replace: true
  controller: 'NavCtrl'
  templateUrl: "#{ CONST.URL_PREFIX }/app/toast.html"
  link: (scope, element, attrs) ->
    scope.toasts = stToast.toasts
])
